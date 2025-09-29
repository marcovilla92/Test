const menuToggle = document.querySelector('.menu-toggle');
const navList = document.querySelector('nav ul');

if (menuToggle && navList) {
  menuToggle.addEventListener('click', () => {
    navList.classList.toggle('open');
    const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
    menuToggle.setAttribute('aria-expanded', (!expanded).toString());
  });
}

const yearSpan = document.querySelector('[data-year]');
if (yearSpan) {
  yearSpan.textContent = new Date().getFullYear().toString();
}

const heroForm = document.getElementById('hero-quick-form');
const contactForm = document.getElementById('contact-form');
const heroFeedback = document.getElementById('hero-form-feedback');

if (heroForm && contactForm) {
  heroForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const mapping = {
      'hero-nome': 'nome',
      'hero-email': 'email',
      'hero-telefono': 'telefono',
    };

    Object.entries(mapping).forEach(([sourceId, targetId]) => {
      const source = document.getElementById(sourceId);
      const target = document.getElementById(targetId);
      if (source && target) {
        target.value = source.value;
      }
    });

    const heroService = document.getElementById('hero-servizio');
    const contactService = document.getElementById('servizio');
    if (heroService && contactService) {
      contactService.value = heroService.value;
    }

    const contactMessage = document.getElementById('messaggio');
    if (contactMessage && !contactMessage.value.trim()) {
      let selectedText = 'Richiesta generica';
      if (heroService && heroService.options && heroService.selectedIndex >= 0) {
        selectedText = heroService.options[heroService.selectedIndex].text;
      }
      contactMessage.value = `Richiesta inviata dal form rapido: ${selectedText}.`;
    }

    if (heroFeedback) {
      heroFeedback.textContent = 'Richiesta ricevuta! Completa i dettagli nel form qui sotto per finalizzare.';
    }

    contactForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => {
      const firstField = contactForm.querySelector('input, select, textarea');
      firstField?.focus();
    }, 600);
  });
}

const serviceForm = document.getElementById('service-quick-form');
const serviceFeedback = document.getElementById('service-form-feedback');

if (serviceForm) {
  serviceForm.addEventListener('submit', (event) => {
    event.preventDefault();
    if (serviceFeedback) {
      serviceFeedback.textContent = 'Richiesta registrata! Ti contatteremo entro 30 minuti lavorativi.';
    }
  });
}

const sidebarForm = document.querySelector('.service-sidebar form');
if (sidebarForm) {
  const feedback = document.createElement('p');
  feedback.className = 'form-feedback';
  feedback.setAttribute('role', 'status');
  feedback.setAttribute('aria-live', 'polite');
  sidebarForm.append(feedback);

  sidebarForm.addEventListener('submit', (event) => {
    event.preventDefault();
    feedback.textContent = 'Grazie! Un consulente ti invierà disponibilità e quotazione entro breve.';
  });
}
