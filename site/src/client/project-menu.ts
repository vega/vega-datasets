/** Native disclosure keeps the project menu usable on touch and without JavaScript. */
export function enhanceProjectMenu(menu: HTMLDetailsElement): void {
  const trigger = menu.querySelector("summary")!;
  const doc = menu.ownerDocument;
  doc.addEventListener("click", (event) => {
    if (event.target instanceof Node && !menu.contains(event.target)) menu.open = false;
  });
  menu.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !menu.open) return;
    menu.open = false;
    trigger.focus();
    event.preventDefault();
  });
  menu.addEventListener("focusout", (event) => {
    if (event.relatedTarget instanceof Node && !menu.contains(event.relatedTarget)) menu.open = false;
  });
}
