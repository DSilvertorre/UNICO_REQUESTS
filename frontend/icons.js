(function () {
  const icons = {
    "calendar-range": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M8 14h3M14 14h2M8 18h2"/>',
    "chart-no-axes-combined": '<path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 16V9"/><path d="M12 16V6"/><path d="M16 16v-4"/><path d="M20 16V8"/>',
    "clipboard-list": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M8 11h8M8 16h8"/>',
    copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><rect x="2" y="2" width="13" height="13" rx="2"/>',
    "key-round": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M15 7l2 2M17 5l2 2"/>',
    "map-pinned": '<path d="M14 18l-5-2-6 3V5l6-3 6 2 6-3v14l-3 1"/><path d="M9 2v14M15 4v5"/><path d="M18 22s4-4 4-7a4 4 0 0 0-8 0c0 3 4 7 4 7Z"/><circle cx="18" cy="15" r="1"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    rocket: '<path d="M4.5 16.5c-1 1-1.5 3-1.5 3s2-.5 3-1.5"/><path d="M9 15l-4-4 3-6 5 5"/><path d="M14 10l5-5s2 4-1 8c-3 4-8 5-8 5l-4-4s1-5 5-8c4-3 8-1 8-1"/><circle cx="15" cy="9" r="1"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    sheet: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h5"/>',
    "table-2": '<path d="M9 3v18M3 9h18M3 15h18"/><rect x="3" y="3" width="18" height="18" rx="2"/>',
    "user-round-check": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M16 11l2 2 4-4"/>',
    "user-round-search": '<circle cx="10" cy="7" r="4"/><path d="M2 21v-2a4 4 0 0 1 4-4h4"/><circle cx="17" cy="17" r="3"/><path d="M21 21l-2-2"/>',
    "users-round": '<path d="M18 21a5 5 0 0 0-10 0"/><circle cx="13" cy="7" r="4"/><path d="M22 21a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/><path d="M2 21a4 4 0 0 1 3-3.87"/><path d="M8 3.13a4 4 0 0 0 0 7.75"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
  };

  function createIcons() {
    document.querySelectorAll("i[data-lucide]").forEach((node) => {
      const name = node.getAttribute("data-lucide");
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "0 0 24 24");
      svg.setAttribute("fill", "none");
      svg.setAttribute("stroke", "currentColor");
      svg.setAttribute("stroke-width", "2");
      svg.setAttribute("stroke-linecap", "round");
      svg.setAttribute("stroke-linejoin", "round");
      svg.setAttribute("aria-hidden", "true");
      svg.innerHTML = icons[name] || icons.search;
      node.replaceWith(svg);
    });
  }

  window.lucide = { createIcons };
})();
