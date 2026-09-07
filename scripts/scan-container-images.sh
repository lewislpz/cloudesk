#!/bin/sh
set -eu

output_directory=${1:?usage: scan-container-images.sh OUTPUT_DIRECTORY}
mkdir -p "$output_directory"
for image in clouddesk-api:test clouddesk-web:test; do
  inventory="$output_directory/${image%:*}.cdx.json"
  go run github.com/anchore/syft/cmd/syft@v1.51.1 "docker:$image" -o cyclonedx-json > "$inventory"
  go run github.com/anchore/grype/cmd/grype@v0.118.0 "sbom:$inventory" --fail-on high
done
