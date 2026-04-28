package com.skillslab.jspring.grading;

import com.skillslab.jspring.order.Customer;
import com.skillslab.jspring.order.Order;
import com.skillslab.jspring.order.OrderService;
import com.skillslab.jspring.order.OrderSummary;
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.PersistenceContext;
import org.hibernate.SessionFactory;
import org.hibernate.stat.Statistics;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.TestPropertySource;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Hidden grading test for exercise-01-fix-n-plus-one.
 *
 * Asserts that OrderService.getRecentOrders() does NOT exhibit the N+1
 * query pattern, by inspecting Hibernate's prepared-statement count.
 *
 * Starter (planted bug):    21 prepared statements for 20 orders.
 * Fixed (@EntityGraph or JOIN FETCH):    1 prepared statement.
 *
 * The assertion fails if the count exceeds 2 — generous to allow either
 * canonical fix shape (single JOIN FETCH = 1, or @EntityGraph with a
 * separate count query = 2).
 */
@SpringBootTest
@Testcontainers
@TestPropertySource(properties = {
        "spring.jpa.properties.hibernate.generate_statistics=true",
        "spring.jpa.hibernate.ddl-auto=create-drop"
})
@DirtiesContext
@DisplayName("[grading] Exercise 01 — fix the N+1 in OrderService.getRecentOrders")
class HiddenQueryCountGradingTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private EntityManagerFactory emf;

    @Autowired
    private OrderService orderService;

    @PersistenceContext
    private EntityManager em;

    @BeforeEach
    @Transactional
    void seedAndResetStats() {
        // Clean slate. ddl-auto=create-drop already gives a fresh schema per
        // suite, but @BeforeEach ensures intra-suite tests don't pollute.
        em.createQuery("delete from Order").executeUpdate();
        em.createQuery("delete from Customer").executeUpdate();

        // Seed 20 customers, each with 1 order. The lazy-fetched Customer
        // is what triggers the N+1 in the starter.
        for (int i = 0; i < 20; i++) {
            Customer c = new Customer();
            c.setName("customer-" + i);
            c.setEmail("user" + i + "@example.com");
            em.persist(c);

            Order o = new Order();
            o.setCustomer(c);
            o.setTotal(BigDecimal.valueOf(100L + i));
            o.setCreatedAt(Instant.now().minusSeconds(60L * i));
            em.persist(o);
        }
        em.flush();
        em.clear();

        // Reset stats AFTER the seed so we count only the SUT's queries.
        Statistics stats = emf.unwrap(SessionFactory.class).getStatistics();
        stats.setStatisticsEnabled(true);
        stats.clear();
    }

    @Test
    @DisplayName("getRecentOrders should run ≤ 2 SQL statements regardless of order count")
    void noNPlusOneOnGetRecentOrders() {
        List<OrderSummary> result = orderService.getRecentOrders();

        Statistics stats = emf.unwrap(SessionFactory.class).getStatistics();
        long prepared = stats.getPrepareStatementCount();

        assertThat(result)
                .as("must return all 20 seeded orders")
                .hasSize(20);

        assertThat(prepared)
                .as("getRecentOrders() should NOT issue N+1 queries — "
                  + "expected ≤ 2 SQL statements, got %d for 20 orders. "
                  + "Use @EntityGraph(attributePaths={\"customer\"}) on the "
                  + "OrderRepository finder, OR rewrite with JOIN FETCH.", prepared)
                .isLessThanOrEqualTo(2);
    }

    @Test
    @DisplayName("customer names in the response match seeded values")
    void customerNamesAccurate() {
        List<OrderSummary> result = orderService.getRecentOrders();
        assertThat(result).hasSize(20);
        assertThat(result)
                .extracting(OrderSummary::customerName)
                .allMatch(name -> name != null && name.startsWith("customer-"));
    }
}
