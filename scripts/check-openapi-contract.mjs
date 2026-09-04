import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import { parse } from 'yaml';

const specSource = process.env.OPENAPI_SPEC ?? new URL('../backend/api/openapi.yaml', import.meta.url);
const spec = parse(await readFile(specSource, 'utf8'));
const serializedSpec = JSON.stringify(spec);

assert.match(spec.openapi, /^3\.1\./, 'the canonical contract must use OpenAPI 3.1');
assert.ok(!serializedSpec.includes('X-Organization-ID'), 'tenant authority must not use a header');
assert.ok(spec.paths['/health/live']?.get, 'the liveness operation must be defined');
assert.ok(spec.paths['/health/ready']?.get, 'the readiness operation must be defined');

const operationIds = new Set();

for (const [path, pathItem] of Object.entries(spec.paths)) {
  for (const method of ['get', 'post', 'put', 'patch', 'delete']) {
    const operation = pathItem[method];
    if (!operation) continue;

    assert.ok(operation.operationId, `${method.toUpperCase()} ${path} must define operationId`);
    assert.ok(!operationIds.has(operation.operationId), `duplicate operationId: ${operation.operationId}`);
    operationIds.add(operation.operationId);

    for (const [status, response] of Object.entries(operation.responses)) {
      const resolved = response.$ref
        ? spec.components.responses[response.$ref.split('/').at(-1)]
        : response;
      assert.ok(
        resolved.headers?.['X-Request-ID'],
        `${method.toUpperCase()} ${path} response ${status} must return X-Request-ID`,
      );
    }

    if (path.startsWith('/health/')) {
      assert.deepEqual(operation.security, [], `${method.toUpperCase()} ${path} must be public`);
      continue;
    }

    assert.ok(
      Object.keys(operation.responses).some((status) => /^4\d\d$/.test(status)),
      `${method.toUpperCase()} ${path} must document a 4xx response`,
    );
    assert.deepEqual(
      operation.security,
      [{ cookieSession: [] }],
      `${method.toUpperCase()} ${path} must require the opaque session cookie`,
    );

    if (['post', 'put', 'patch', 'delete'].includes(method)) {
      const parameters = [...(pathItem.parameters ?? []), ...(operation.parameters ?? [])];
      assert.ok(
        parameters.some((parameter) => parameter.$ref === '#/components/parameters/CsrfToken'),
        `${method.toUpperCase()} ${path} must require the shared CSRF header`,
      );
    }
  }

  if (!path.includes('{organizationId}')) continue;

  assert.match(path, /^\/api\/v1\/organizations\/\{organizationId\}(?:\/|$)/);
  const organizationParameter = pathItem.parameters?.find(
    (parameter) => parameter.$ref === '#/components/parameters/OrganizationId',
  );
  assert.ok(organizationParameter, `${path} must use the shared OrganizationId path parameter`);
}

assert.ok(operationIds.size >= 3, 'the compatibility fixture must cover health and a tenant operation');
assert.equal(
  spec.components.securitySchemes.cookieSession.in,
  'cookie',
  'browser authentication must remain an opaque cookie scheme',
);
assert.equal(spec.components.securitySchemes.cookieSession.type, 'apiKey');
assert.equal(spec.components.securitySchemes.cookieSession.name, '__Host-cloudesk_session');

const visit = (value) => {
  if (!value || typeof value !== 'object') return;
  if (typeof value.$ref === 'string') {
    assert.ok(value.$ref.startsWith('#/'), `external OpenAPI reference is forbidden: ${value.$ref}`);
  }
  for (const child of Object.values(value)) visit(child);
};

visit(spec);

console.log(`validated ${operationIds.size} OpenAPI operations and ClouDesk contract invariants`);
