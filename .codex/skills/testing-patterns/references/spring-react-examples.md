---
name: testing-patterns
description: Use when adding or reviewing Spring Boot or React tests, test levels, mocks, fixtures, or TDD workflows.
---

# Testing Patterns and Utilities

## Testing Philosophy

**Test-Driven Development (TDD):**
- Write failing test FIRST
- Implement minimal code to pass
- Refactor after green
- Never write production code without a failing test

**Behavior-Driven Testing:**
- Test behavior, not implementation
- Focus on user requirements and API contracts
- Avoid testing internal private methods
- Use descriptive test names (Gherkin style: `should... when...`)

**Modern Mocking Strategy:**
- **Backend**: Use `@Mock` and `@InjectMocks` (Mockito). Use `@MockBean` for slice tests.
- **Frontend**: Use **Mock Service Worker (MSW)** for API mocking. Focus on UI interactions via RTL.

---

## ☕ Backend Testing (Spring Boot)

### 1. Service Layer (Unit)
Use `MockitoExtension` and mock repositories. Use AssertJ for fluent assertions.

```java
@ExtendWith(MockitoExtension.class)
class MyServiceTest {
    @Mock private MyRepository repository;
    @InjectMocks private MyService service;

    @Test
    void shouldReturnData_WhenIdExists() {
        // Given
        var entity = MyFactory.createEntity(1L);
        when(repository.findById(1L)).thenReturn(Optional.of(entity));
        
        // When
        var result = service.getById(1L);
        
        // Then
        assertThat(result).isNotNull();
        assertThat(result.getName()).isEqualTo(entity.getName());
    }
}
```

### 2. Controller Layer (Slice)
Use `@WebMvcTest` to test only the web layer and its security.

```java
@WebMvcTest(MyController.class)
class MyControllerTest {
    @Autowired private MockMvc mockMvc;
    @MockBean private MyService service;

    @Test
    @WithMockUser // For security-enabled endpoints
    void shouldReturn200_WhenGetCalled() throws Exception {
        mockMvc.perform(get("/api/data"))
            .andExpect(status().isOk());
    }
}
```

### 3. Persistence Layer (Slice)
Use `@DataJpaTest` to test repositories and custom queries.

```java
@DataJpaTest
class MyRepositoryTest {
    @Autowired private MyRepository repository;

    @Test
    void shouldSaveAndFind() {
        var entity = new MyEntity("test");
        repository.save(entity);
        assertThat(repository.findByName("test")).isPresent();
    }
}
```

---

## ⚛️ Frontend Testing (React + Vitest)

### 1. Component Testing (React Testing Library)
Focus on the user's perspective. Avoid testing implementation details like state names.

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

it('should call onAction when button clicked', () => {
  const onAction = vi.fn();
  render(<MyComponent onAction={onAction} />);
  
  fireEvent.click(screen.getByRole('button', { name: /action/i }));
  expect(onAction).toHaveBeenCalled();
});
```

### 2. Hook Testing
Use `renderHook` for custom logic.

```typescript
import { renderHook, act } from '@testing-library/react';
import { useMyHook } from './useMyHook';

it('should increment count', () => {
  const { result } = renderHook(() => useMyHook());
  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});
```

### 3. API Mocking (MSW)
Prefer MSW over manual mocking of fetch/axios.

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/items', () => {
    return HttpResponse.json([{ id: 1, name: 'Bomba' }]);
  }),
];
```

---

## 🏭 Factory Pattern (Professional Data)

### Java (Builders)
```java
public class TapaFactory {
    public static Tapa createTapa(Long id) {
        return Tapa.builder()
            .id(id)
            .name("Tapa " + id)
            .build();
    }
}
```

### TypeScript (Overrides)
```typescript
export const createMockTapa = (overrides?: Partial<Tapa>): Tapa => ({
  id: 1,
  name: 'Default Tapa',
  organization: { id: 1, name: 'Example Organization' },
  ...overrides,
});
```

---

## 🚥 Verification Workflow

1.  **RED**: Write a failing test for the new requirement.
2.  **GREEN**: Implement minimal code to make the test pass.
3.  **REFACTOR**: Improve structure without changing behavior.
4.  **COVERAGE**: Ensure branches and edge cases are covered.

```bash
# Backend execution
./mvnw test

# Frontend execution
npm test
```
