import { LitElement, css, html } from "lit";

export class LocationIntelligenceCard extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: 1rem;
      border-radius: 1rem;
      background:
        radial-gradient(circle at top left, rgba(76, 133, 212, 0.16), transparent 40%),
        linear-gradient(145deg, #101722, #192433);
      color: #f5f7fb;
      font-family: "IBM Plex Sans", sans-serif;
    }

    .eyebrow {
      font-size: 0.75rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      opacity: 0.7;
    }

    h2 {
      margin: 0.4rem 0 0.75rem;
      font-size: 1.15rem;
    }

    p {
      margin: 0;
      line-height: 1.5;
      opacity: 0.9;
    }
  `;

  render() {
    return html`
      <div class="eyebrow">Location Intelligence</div>
      <h2>Spatial awareness card scaffold</h2>
      <p>
        Backend entities and fusion logic are scaffolded. This card workspace is
        ready for compass, map, subject list, and history views.
      </p>
    `;
  }
}

customElements.define("location-intelligence-card", LocationIntelligenceCard);

