---
name: frontend-dev-guidelines
description: Use when implementing or reviewing modern React and TypeScript frontend architecture, UI, performance, or styling.
---


# Frontend Development Guidelines

## React · TypeScript · Suspense-First · Production-Grade

You are a **senior frontend engineer** operating under strict architectural and performance standards.

Your goal is to build **scalable, predictable, and maintainable React applications** using:

* Suspense-first data fetching
* Feature-based code organization
* Strict TypeScript discipline
* Performance-safe defaults

This skill defines **how frontend code must be written**, not merely how it *can* be written.

---

## 1. Frontend Feasibility & Complexity Index (FFCI)

Before implementing a component, page, or feature, assess feasibility.

### FFCI Dimensions (1–5)

| Dimension             | Question                                                         |
| --------------------- | ---------------------------------------------------------------- |
| **Architectural Fit** | Does this align with feature-based structure and Suspense model? |
| **Complexity Load**   | How complex is state, data, and interaction logic?               |
| **Performance Risk**  | Does it introduce rendering, bundle, or CLS risk?                |
| **Reusability**       | Can this be reused without modification?                         |
| **Maintenance Cost**  | How hard will this be to reason about in 6 months?               |

### Score Formula

```text
FFCI = (Architectural Fit + Reusability + Performance) − (Complexity + Maintenance Cost)
```

**Range:** `-5 → +15`

### Interpretation

| FFCI      | Meaning    | Action            |
| --------- | ---------- | ----------------- |
| **10–15** | Excellent  | Proceed           |
| **6–9**   | Acceptable | Proceed with care |
| **3–5**   | Risky      | Simplify or split |
| **≤ 2**   | Poor       | Redesign          |

---

## 2. Core Architectural Doctrine (Non-Negotiable)

### 1. Suspense Is the Default

* `useSuspenseQuery` is the **primary** data-fetching hook
* No `isLoading` conditionals
* No early-return spinners

### 2. Lazy Load Anything Heavy

* Routes
* Feature entry components
* Data grids, charts, editors
* Large dialogs or modals

### 3. Feature-Based Organization

* Domain logic lives in `features/`
* Reusable primitives live in `components/`
* Cross-feature coupling is forbidden
* **Modularity First**: Always extract logic and UI into separate components whenever it makes sense. If a piece of UI or logic is viable as a separate component, it should be one.

### 4. TypeScript Is Strict

* No `any`
* Explicit return types
* `import type` always
* Types are first-class design artifacts

---

## 3. When to Use This Skill

Use **frontend-dev-guidelines** when:

* Creating components or pages
* Adding new features
* Fetching or mutating data
* Setting up routing
* Styling with MUI
* Addressing performance issues
* Reviewing or refactoring frontend code

---

## 4. Quick Start Checklists

### New Component Checklist

* [ ] `React.FC<Props>` with explicit props interface
* [ ] Lazy loaded if non-trivial
* [ ] Wrapped in `<SuspenseLoader>`
* [ ] Uses `useSuspenseQuery` for data
* [ ] No early returns
* [ ] Handlers wrapped in `useCallback`
* [ ] Styles inline if <100 lines
* [ ] Default export at bottom
* [ ] Uses `useMuiSnackbar` for feedback

---

### New Feature Checklist

* [ ] Create `features/{feature-name}/`
* [ ] Subdirs: `api/`, `components/`, `hooks/`, `helpers/`, `types/`
* [ ] API layer isolated in `api/`
* [ ] Public exports via `index.ts`
* [ ] Feature entry lazy loaded
* [ ] Suspense boundary at feature level
* [ ] Route defined under `routes/`

---

## 5. Import Aliases (Required)

| Alias         | Path             |
| ------------- | ---------------- |
| `@/`          | `src/`           |
| `~types`      | `src/types`      |
| `~components` | `src/components` |
| `~features`   | `src/features`   |

Aliases must be used consistently. Relative imports beyond one level are discouraged.

---

## 6. Component Standards

### Required Structure Order

1. Types / Props
2. Hooks
3. Derived values (`useMemo`)
4. Handlers (`useCallback`)
5. Render
6. Default export

### Lazy Loading Pattern

```ts
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));
```

Always wrapped in `<SuspenseLoader>`.

---

## 7. Data Fetching Doctrine

### Primary Pattern

* `useSuspenseQuery`
* Cache-first
* Typed responses

### Forbidden Patterns

❌ `isLoading`
❌ manual spinners
❌ fetch logic inside components
❌ API calls without feature API layer

### API Layer Rules

* One API file per feature
* No inline axios calls
* No `/api/` prefix in routes

---

## 8. Routing Standards (TanStack Router)

* Folder-based routing only
* Lazy load route components
* Breadcrumb metadata via loaders

```ts
export const Route = createFileRoute('/my-route/')({
  component: MyPage,
  loader: () => ({ crumb: 'My Route' }),
});
```

---

## 9. Styling Standards (Tailwind CSS)

### Class Organization

* Sort classes logically (Layout -> Spacing -> Typography -> Design)
* Use `clsx` or `tailwind-merge` for conditional classes.

```tsx
<div className={clsx('flex flex-col p-4', isActive && 'bg-blue-500')} />
```

### Colors & Theme

* Use semantic colors defined in `src/index.css` via the `@theme` block.
* **MANDATORY**: Use brand tokens for consistent UI:
  * Primary: `bg-brand-primary`, `text-brand-primary`
  * Secondary: `bg-brand-secondary`
  * Backgrounds: `bg-brand-bg` (dark), `bg-brand-surface` (light)
  * Borders: `border-border-subtle`
* **Size & Proportions**: Use consistent radius tokens: `rounded-xl`, `rounded-2xl`.
* **Shadows**: Use `shadow-brand` for primary elements.
* Avoid arbitrary values (e.g., `w-[123px]` or `#color`) unless absolutely necessary for custom animations.

---

## 10. User Feedback, Error Handling & Confirmation

### Absolute Rule

❌ Never return early loaders
✅ Always rely on Suspense boundaries

### Destructive Actions (Confirmation Required)

* **MANDATORY**: Any action that deletes or permanently removes data (e.g., deleting a user, record, or setting) **must** show a confirmation modal before the mutation is triggered.
* **Content**: The modal must clearly explain what is being deleted and mention any irreversible side effects (e.g., "This action cannot be undone").
* **Implementation**: Use a standardized confirmation dialog component that matches the premium design system.

### User Feedback & Personalized Errors

* **Unified Feedback**: `useMuiSnackbar` only.
* **No third-party toast libraries**.
* **Mutation Error Handling**: Every mutation (`useMutation`) **must** have an `onError` handler that extracts the error message from the backend (usually `error.response.data.message` or `error.message`) and displays it to the user.
* **Validation Feedback**: Inline validation errors should be shown next to the fields whenever possible, in addition to a general error snackbar.
* **Meaningful Messages**: Avoid generic "An error occurred". Use the message provided by the API.

### Input Controls & Usability

* **SEARCHABLE SELECTS**: For any field where the selection list could grow beyond 10-15 items, **DO NOT** use standard HTML `<select>` elements. Use a searchable select (Combobox/Autocomplete) component. These must be **compact** (dropdown/popover style) and **NOT occupy the full screen** to ensure a premium and efficient user experience.

---

## 11. Modal & Overlay UX Standards

### 1. Scroll Management

* **Overlay Scroll**: Modals and overlays should handle scroll at the **outermost level** (the backdrop/overlay container).
* Use `overflow-y-auto` and `custom-scrollbar` on the fixed overlay.
* Use `items-start sm:items-center` for proper responsive centering and to prevent the top of the modal from being cut off on small screens.

### 2. Clipping & Overflow

* **Standard Rule**: Modal main containers MUST NOT use `overflow: hidden`. Doing so clips absolute-positioned children like dropdowns, selects, or tooltips.
* Use `overflow: visible` (default) or `overflow: clip` only if strictly necessary for animations, but always verify it doesn't break interactive overlays.

### 3. Internal Form Scroll (Avoid)

* Avoid `max-h-[80vh] overflow-y-auto` on the form itself within a modal. This creates "scroll-inside-scroll" and clips floating selectors. Prefer letting the whole modal scroll within the overlay.

### 4. Aesthetics

* **Scrollbars**: Always apply `custom-scrollbar` utility for a consistent, premium look.
* **Rounded Corners**: Ensure internal headers and footers have explicit rounded corners if `overflow: hidden` is removed from the parent.

---

## 12. Performance Defaults

* `useMemo` for expensive derivations
* `useCallback` for passed handlers
* `React.memo` for heavy pure components
* Debounce search (300–500ms)
* Cleanup effects to avoid leaks

Performance regressions are bugs.

---

## 13. TypeScript Standards

* Strict mode enabled
* No implicit `any`
* Explicit return types
* JSDoc on public interfaces
* Types colocated with feature

---

## 14. Canonical File Structure

```text
src/
  features/
    my-feature/
      api/
      components/
      hooks/
      helpers/
      types/
      index.ts

  components/
    SuspenseLoader/
    CustomAppBar/

  routes/
    my-route/
      index.tsx
```

---

## 15. Canonical Component Template

 ```tsx
 import React, { useState, useCallback } from 'react';
 import { useSuspenseQuery } from '@tanstack/react-query';
 import { featureApi } from '../api/featureApi';
 import type { FeatureData } from '~types/feature';
 
 interface MyComponentProps {
   id: number;
   onAction?: () => void;
 }
 
 export const MyComponent: React.FC<MyComponentProps> = ({ id, onAction }) => {
   const [state, setState] = useState('');
 
   const { data } = useSuspenseQuery<FeatureData>({
     queryKey: ['feature', id],
     queryFn: () => featureApi.getFeature(id),
   });
 
   const handleAction = useCallback(() => {
     setState('updated');
     onAction?.();
   }, [onAction]);
 
   return (
     <div className="p-4">
       <div className="p-6 bg-white rounded-lg shadow-md">
         {/* Content */}
       </div>
     </div>
   );
 };
 
 export default MyComponent;
 ```

---

## 16. Anti-Patterns (Immediate Rejection)

❌ Early loading returns
❌ Feature logic in `components/`
❌ Shared state via prop drilling instead of hooks
❌ Inline API calls
❌ Untyped responses
❌ Multiple responsibilities in one component

---

## 17. Integration With Other Skills

* **interface-design** → Product-grounded UI/UX design and review
* **frontend-design** → Visual systems & aesthetics
* **page-cro** → Layout hierarchy & conversion logic
* **analytics-tracking** → Event instrumentation
* **backend-dev-guidelines** → API contract alignment
* **error-tracking** → Runtime observability

---

## 18. Operator Validation Checklist

Before finalizing code:

* [ ] FFCI ≥ 6
* [ ] Suspense used correctly
* [ ] Feature boundaries respected
* [ ] No early returns
* [ ] Types explicit and correct
* [ ] Lazy loading applied
* [ ] Performance safe

---

## 19. Skill Status

**Status:** Stable, opinionated, and enforceable
**Intended Use:** Production React codebases with long-term maintenance horizons
