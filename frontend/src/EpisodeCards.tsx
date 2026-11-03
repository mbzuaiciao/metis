import type { Episode } from "./types";

export function EpisodeCards({ episodes }: { episodes: Episode[] }) {
  return (
    <div className="episode-grid">
      {episodes.map((h) => (
        <article key={h.id} className="episode">
          <span className="eyebrow">{h.period} · Historical context</span>
          <h3>{h.title}</h3>
          <p>{h.fact}</p>
          <p>
            <b>Portfolio lens</b> {h.interpretation}
          </p>
          <small>{h.limitation}</small>
          <a href={h.source_url} target="_blank" rel="noreferrer">
            {h.source_title} ↗
          </a>
        </article>
      ))}
    </div>
  );
}
