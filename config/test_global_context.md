Favor Unit Tests: The highest priority is generating unit tests. These tests must be fast, deterministic, and run in isolation. They should focus on a single unit of work (one function or method) and mock all external dependencies such as databases, network calls, and file systems.

Test the Public Interface, Not the Implementation: Agents must generate tests that validate the public-facing behavior of a module. The tests should confirm that for a given input, the function produces the expected output or side effect. Do not test private functions or internal state.

Identify and Report Untestable Code: If a section of code is difficult to test, do not generate a complex or brittle test. Instead, the agent's primary responsibility is to:

Clearly identify the code as "untestable" or "difficult to test."

Explain why it is untestable (e.g., hard-coded dependencies, reliance on global state, mixing logic with side effects).

Recommend Refactoring Before Testing: When untestable code is identified, the agent must suggest a specific, actionable refactoring that would make the code testable.

Example Suggestion: "The processPayment function is untestable because it directly calls new DatabaseConnection(). Recommend refactoring to accept the database connection as a parameter (dependency injection) before writing tests."

Coverage is a Tool, Not a Target: Do not write tests for trivial code (e.g., simple getters/setters) or code with no logic. If a coverage gap is not worth testing, explicitly state that it is being skipped and why. A test suite's value comes from preventing regressions in critical logic, not from reaching 100% coverage.

Clarity and Structure: All generated tests must be clear, readable, and follow the Arrange-Act-Assert (AAA) pattern:

Arrange: Set up all necessary preconditions and inputs.

Act: Execute the function or method being tested.

Assert: Verify that the outcome is as expected.