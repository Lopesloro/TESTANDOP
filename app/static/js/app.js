// O conteúdo nasce no HTML. Este script só troca estado: header sólido após 80px
// e a régua de cada seção crescendo quando ela entra na tela.
(function () {
  var topo = document.querySelector("[data-topo]");
  if (topo && topo.classList.contains("topo--sobre-hero")) {
    var aplicar = function () {
      topo.classList.toggle("solido", window.scrollY > 80);
    };
    aplicar();
    window.addEventListener("scroll", aplicar, { passive: true });
  }

  var secoes = document.querySelectorAll("[data-revelar]");
  var mostrar = function (el) { el.classList.add("visivel"); };

  if (!("IntersectionObserver" in window)) {
    secoes.forEach(mostrar);
    return;
  }

  var observador = new IntersectionObserver(function (entradas) {
    entradas.forEach(function (entrada) {
      if (entrada.isIntersecting) {
        mostrar(entrada.target);
        observador.unobserve(entrada.target);
      }
    });
  }, { threshold: 0.18 });

  secoes.forEach(function (el) { observador.observe(el); });
})();
