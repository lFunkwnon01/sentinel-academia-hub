<script setup lang="ts">
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="min-h-screen bg-white">
    <!-- Top nav -->
    <header class="border-b border-ink-100">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center">
            <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <span class="font-semibold text-ink-900">Sentinel AcademIA</span>
        </div>
        <nav class="flex items-center gap-6 text-sm">
          <a href="#features" class="text-ink-600 hover:text-ink-900">Caracter\'isticas</a>
          <a href="#how" class="text-ink-600 hover:text-ink-900">C\'omo funciona</a>
          <RouterLink to="/dashboard" class="btn-secondary">Ingresar</RouterLink>
        </nav>
      </div>
    </header>

    <!-- Hero -->
    <section class="relative overflow-hidden">
      <div class="absolute inset-0 -z-10">
        <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-br from-brand-50 via-transparent to-transparent rounded-full blur-3xl opacity-60"></div>
      </div>
      <div class="max-w-6xl mx-auto px-6 py-20 lg:py-28 text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-medium mb-6 border border-brand-100">
          <span class="w-1.5 h-1.5 rounded-full bg-brand-500"></span>
          Plataforma universitaria con IA
        </div>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-semibold text-ink-900 tracking-tight leading-tight max-w-4xl mx-auto">
          Tu voz. Nuestra IA.
          <span class="bg-gradient-to-r from-brand-600 to-brand-800 bg-clip-text text-transparent">Universidad m\'as justa.</span>
        </h1>
        <p class="mt-6 text-lg text-ink-600 max-w-2xl mx-auto leading-relaxed">
          Sentinel AcademIA analiza cada queja con inteligencia artificial, categoriza
          prioridades y la env\'ia a la autoridad correcta. En minutos, no semanas.
        </p>
        <div class="mt-10 flex items-center justify-center gap-3">
          <RouterLink to="/queja" class="btn-primary text-base px-6 py-3">
            Reportar una queja
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
            </svg>
          </RouterLink>
          <RouterLink to="/dashboard" class="btn-secondary text-base px-6 py-3">Ver dashboard</RouterLink>
        </div>
        <div class="mt-12 grid grid-cols-3 gap-8 max-w-2xl mx-auto">
          <div>
            <div class="text-3xl font-semibold text-ink-900">6</div>
            <div class="text-sm text-ink-500 mt-1">Categor\'ias</div>
          </div>
          <div>
            <div class="text-3xl font-semibold text-ink-900">&lt; 30s</div>
            <div class="text-sm text-ink-500 mt-1">Tiempo de an\'alisis</div>
          </div>
          <div>
            <div class="text-3xl font-semibold text-ink-900">10+</div>
            <div class="text-sm text-ink-500 mt-1">Universidades soportadas</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="py-20 bg-ink-50">
      <div class="max-w-6xl mx-auto px-6">
        <div class="text-center max-w-2xl mx-auto mb-12">
          <h2 class="text-3xl font-semibold text-ink-900 tracking-tight">Dise\~nado para universidades reales</h2>
          <p class="mt-3 text-ink-600">No es solo un formulario. Es un sistema completo de gesti\'on de quejas con inteligencia artificial.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div v-for="f in features" :key="f.title" class="card p-6">
            <div :class="['w-10 h-10 rounded-lg flex items-center justify-center mb-4', f.iconBg]">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="f.icon" />
              </svg>
            </div>
            <h3 class="font-semibold text-ink-900">{{ f.title }}</h3>
            <p class="mt-2 text-sm text-ink-600 leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="how" class="py-20">
      <div class="max-w-6xl mx-auto px-6">
        <h2 class="text-3xl font-semibold text-ink-900 tracking-tight text-center mb-12">C\'omo funciona</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div v-for="(s, i) in steps" :key="i" class="relative">
            <div class="card p-5 h-full">
              <div class="text-xs font-bold text-brand-600 mb-2">PASO {{ i + 1 }}</div>
              <div class="font-medium text-ink-900">{{ s.title }}</div>
              <div class="mt-2 text-sm text-ink-500">{{ s.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20 bg-gradient-to-br from-brand-600 to-brand-800 text-white">
      <div class="max-w-3xl mx-auto px-6 text-center">
        <h2 class="text-3xl font-semibold tracking-tight">Empieza a transformar tu universidad</h2>
        <p class="mt-3 text-brand-100">Menos burocracia, m\'as confianza. M\'as justicia.</p>
        <RouterLink to="/queja" class="mt-8 inline-flex items-center gap-2 bg-white text-brand-700 font-medium px-6 py-3 rounded-lg hover:bg-brand-50 transition-colors">
          Reportar primera queja
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
          </svg>
        </RouterLink>
      </div>
    </section>

    <footer class="border-t border-ink-100 py-8">
      <div class="max-w-6xl mx-auto px-6 text-sm text-ink-500 flex items-center justify-between">
        <div>&copy; 2026 Sentinel AcademIA &middot; Hackat\'on Multi-nube AWS + OCI</div>
        <div>Hecho con <span class="text-red-500">&hearts;</span> para universidades</div>
      </div>
    </footer>
  </div>
</template>

<script lang="ts">
export default {
  name: 'HomeView',
  data() {
    return {
      features: [
        {
          title: 'An\'alisis con IA',
          desc: 'Cohere categoriza y prioriza cada queja en menos de 30 segundos. Sin sesgo, sin demoras.',
          icon: 'M13 10V3L4 14h7v7l9-11h-7z',
          iconBg: 'bg-gradient-to-br from-brand-500 to-brand-700',
        },
        {
          title: 'Multi-tenant',
          desc: 'Cada universidad tiene sus propias reglas, autoridades y reportes. Privado y aislado.',
          icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
          iconBg: 'bg-gradient-to-br from-purple-500 to-purple-700',
        },
        {
          title: 'Notificaciones a autoridades',
          desc: 'Email autom\'atico a bienestar, rector\'ia, seguridad. Con recomendaciones de acci\'on.',
          icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
          iconBg: 'bg-gradient-to-br from-emerald-500 to-emerald-700',
        },
        {
          title: 'An\'alisis agregado',
          desc: '10 quejas sobre el mismo tema? Se consolidan. Patrones invisibles al ojo humano.',
          icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
          iconBg: 'bg-gradient-to-br from-amber-500 to-amber-700',
        },
        {
          title: 'Dashboard ejecutivo',
          desc: 'M\'etricas en tiempo real: cr\'iticas, pendientes, por categor\'ia. Para rector\'ia.',
          icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
          iconBg: 'bg-gradient-to-br from-pink-500 to-pink-700',
        },
        {
          title: 'RAG con tu reglamento',
          desc: 'Sube el reglamento de tu universidad. La IA responde con tus propias reglas.',
          icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
          iconBg: 'bg-gradient-to-br from-cyan-500 to-cyan-700',
        },
      ],
      steps: [
        { title: 'Reportas', desc: 'Estudiante o personal describe la situaci\'on con su email.' },
        { title: 'IA analiza', desc: 'Cohere categoriza, prioriza y asigna la autoridad.' },
        { title: 'Notifica', desc: 'Email autom\'atico a bienestar, rector\'ia o seguridad.' },
        { title: 'Resuelve', desc: 'La autoridad act\'ua y la comunidad universitaria mejora.' },
      ],
    };
  },
};
</script>
