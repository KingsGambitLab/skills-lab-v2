package PACKAGE_PLACEHOLDER.grading;

// Template hidden grading test for Java/Spring courses.
// Copy this into .grading/exercise-NN-<slug>/ and adapt:
//   - PACKAGE_PLACEHOLDER → the course's main package (e.g. com.skillslab.jspring)
//   - Test class name + assertions
//
// Per CLAUDE.md §"BEHAVIORAL TEST HARNESS": the test asserts the LEARNING
// PROPERTY (performance / security / contract / idempotency / etc.) using
// the framework's NATIVE primitive. NEVER asserts code-shape or annotation
// presence — that's regex on source, not behavior.
//
// Examples by pedagogy (uncomment and adapt):
//
// (1) N+1 detection — Hibernate Statistics primitive:
//     @SpringBootTest
//     @TestPropertySource(properties = {"spring.jpa.properties.hibernate.generate_statistics=true"})
//     class HiddenQueryCountGradingTest {
//         @Autowired EntityManagerFactory emf;
//         @Test void atMostTwoQueries() {
//             Statistics s = emf.unwrap(SessionFactory.class).getStatistics();
//             s.setStatisticsEnabled(true); s.clear();
//             // ... invoke the SUT ...
//             assertThat(s.getPrepareStatementCount()).isLessThanOrEqualTo(2);
//         }
//     }
//
// (2) Auth contract — MockMvc + status assertion:
//     @WebMvcTest(MyController.class)
//     class HiddenAuthGradingTest {
//         @Autowired MockMvc mvc;
//         @Test void unauthenticated_401() throws Exception {
//             mvc.perform(get("/api/admin")).andExpect(status().isUnauthorized());
//         }
//     }
//
// (3) Idempotency contract — MockMvc + repeated POST:
//     @Test void idempotency_key_returns_same_response() throws Exception {
//         String key = "TEST-123";
//         String body = "{\"x\":1}";
//         var r1 = mvc.perform(post("/api/orders").header("Idempotency-Key", key).content(body))
//             .andReturn();
//         var r2 = mvc.perform(post("/api/orders").header("Idempotency-Key", key).content(body))
//             .andReturn();
//         assertThat(r1.getResponse().getContentAsString())
//             .isEqualTo(r2.getResponse().getContentAsString());
//     }
//
// (4) Validation contract — invalid body returns 400 with errors[]:
//     @Test void missing_required_field_returns_400() throws Exception {
//         mvc.perform(post("/api/orders").contentType(APPLICATION_JSON).content("{}"))
//             .andExpect(status().isBadRequest())
//             .andExpect(jsonPath("$.errors").exists());
//     }
//
// All four primitives use only spring-boot-starter-test (already in pom.xml).
// For DB-backed tests, add @Testcontainers + @Container PostgreSQLContainer.

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.fail;

class HiddenTemplateGradingTest {
    @Test
    void replaceThisWithRealAssertion() {
        fail("This is the template hidden test — replace with a real behavior assertion. "
           + "See class comment for examples by pedagogy.");
    }
}
