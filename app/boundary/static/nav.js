// The role menu is a <details>: open on wide screens, folded behind "Menu" on phones.
(function () {
  var menu = document.querySelector(".nav-menu");
  if (!menu || !window.matchMedia) return;
  var narrow = window.matchMedia("(max-width: 44rem)");
  function sync() { menu.open = !narrow.matches; }
  sync();
  if (narrow.addEventListener) narrow.addEventListener("change", sync);
})();
