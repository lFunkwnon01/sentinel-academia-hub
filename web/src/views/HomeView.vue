<script setup lang="ts">
import { RouterLink } from 'vue-router';
import AppButton from '@/components/common/AppButton.vue';
</script>

<template>
  <div class="home">
    <section class="home__hero">
      <div class="home__hero-content">
        <span class="home__badge">Hackaton 2025</span>
        <h1 class="home__title">Sentinel AcademIA</h1>
        <p class="home__subtitle">
          Plataforma universitaria de quejas con IA generativa.
          <br />
          Escuchamos, analizamos y respondemos en tiempo real.
        </p>
        <div class="home__cta">
          <RouterLink to="/queja">
            <AppButton variant="primary" size="lg">Reportar una queja</AppButton>
          </RouterLink>
          <RouterLink to="/dashboard">
            <AppButton variant="secondary" size="lg">Ver dashboard</AppButton>
          </RouterLink>
        </div>
      </div>
      <div class="home__hero-visual" aria-hidden="true">
        <div class="home__visual-card">
          <div class="home__visual-icon">🛡️</div>
          <div class="home__visual-text">Sentinel</div>
        </div>
      </div>
    </section>

    <section class="home__features">
      <h2 class="home__section-title">Caracteristicas principales</h2>
      <div class="home__grid">
        <article class="home__feature">
          <div class="home__feature-icon" aria-hidden="true">🤖</div>
          <h3>Analisis con IA</h3>
          <p>Cohere Command R + Llama 3.1 analizan cada queja en menos de 30 segundos.</p>
        </article>
        <article class="home__feature">
          <div class="home__feature-icon" aria-hidden="true">⚡</div>
          <h3>Deteccion de casos criticos</h3>
          <p>Alertas inmediatas a bienestar universitario cuando se detecta un caso de riesgo.</p>
        </article>
        <article class="home__feature">
          <div class="home__feature-icon" aria-hidden="true">☁️</div>
          <h3>Multi-nube real</h3>
          <p>AWS para orquestacion serverless, Oracle OCI para el modelo de IA generativa.</p>
        </article>
        <article class="home__feature">
          <div class="home__feature-icon" aria-hidden="true">📊</div>
          <h3>Dashboard en tiempo real</h3>
          <p>Metricas agregadas y tendencias para la toma de decisiones institucionales.</p>
        </article>
        <article class="home__feature">
          <div class="home__feature-icon" aria-hidden="true">💬</div>
          <h3>Chat con RAG</h3>
          <p>Asistente conversacional con acceso al reglamento y al historial de quejas.</p>
        </article>
        <article class="home__feature">
          <div class="home__feature-icon" aria-hidden="true">🔒</div>
          <h3>Privacidad por diseño</h3>
          <p>Anonimizacion automatica de personas mencionadas en los analisis.</p>
        </article>
      </div>
    </section>

    <section class="home__stack">
      <h2 class="home__section-title">Stack Tecnologico</h2>
      <div class="home__stack-grid">
        <div class="home__stack-card home__stack-card--aws">
          <h3>AWS</h3>
          <ul>
            <li>Lambda (9 funciones)</li>
            <li>API Gateway HTTP API</li>
            <li>SQS + SNS + EventBridge</li>
            <li>DynamoDB + S3</li>
            <li>CloudWatch + X-Ray</li>
          </ul>
        </div>
        <div class="home__stack-card home__stack-card--oci">
          <h3>Oracle OCI</h3>
          <ul>
            <li>Generative AI (Cohere R)</li>
            <li>Fallback: Llama 3.1 70B</li>
            <li>Document Understanding</li>
            <li>Vault (secretos)</li>
          </ul>
        </div>
        <div class="home__stack-card home__stack-card--fe">
          <h3>Frontend</h3>
          <ul>
            <li>Vue 3 + Composition API</li>
            <li>TypeScript estricto</li>
            <li>Vite + Pinia + Vue Router</li>
            <li>CSS nativo con variables</li>
            <li>Desplegado en Vercel</li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: var(--space-16);
  padding: var(--space-8) 0;
}

.home__hero {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--space-12);
  align-items: center;
  padding: var(--space-12) 0;
}

.home__badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-4);
}

.home__title {
  font-size: var(--text-5xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  line-height: 1.1;
  margin-bottom: var(--space-4);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-info) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.home__subtitle {
  font-size: var(--text-xl);
  color: var(--color-text-muted);
  margin-bottom: var(--space-8);
  line-height: var(--leading-relaxed);
}

.home__cta {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.home__hero-visual {
  display: flex;
  align-items: center;
  justify-content: center;
}

.home__visual-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 220px;
  height: 220px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-info) 100%);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl);
  color: white;
  gap: var(--space-3);
}

.home__visual-icon {
  font-size: 80px;
}

.home__visual-text {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
}

.home__section-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  text-align: center;
  margin-bottom: var(--space-8);
}

.home__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}

.home__feature {
  padding: var(--space-6);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.home__feature:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.home__feature-icon {
  font-size: 36px;
  margin-bottom: var(--space-3);
}

.home__feature h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin-bottom: var(--space-2);
  color: var(--color-text);
}

.home__feature p {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

.home__stack-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--space-6);
}

.home__stack-card {
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border-left: 4px solid;
}

.home__stack-card--aws {
  background: #fff8f0;
  border-left-color: #ff9900;
}

.home__stack-card--oci {
  background: #fef2f2;
  border-left-color: #c74634;
}

.home__stack-card--fe {
  background: #f0f9ff;
  border-left-color: #3b82f6;
}

.home__stack-card h3 {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--space-3);
}

.home__stack-card ul {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text);
}

.home__stack-card li::before {
  content: '✓ ';
  color: var(--color-success);
  font-weight: bold;
  margin-right: var(--space-1);
}

@media (max-width: 768px) {
  .home__hero {
    grid-template-columns: 1fr;
    text-align: center;
    padding: var(--space-6) 0;
  }

  .home__cta {
    justify-content: center;
  }

  .home__title {
    font-size: var(--text-4xl);
  }

  .home__visual-card {
    width: 160px;
    height: 160px;
  }

  .home__visual-icon {
    font-size: 60px;
  }
}
</style>
