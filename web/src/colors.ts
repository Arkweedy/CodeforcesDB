import type { RatingStatus } from "./types";

export type RatingBand =
  | "unrated"
  | "gray"
  | "cyan"
  | "blue"
  | "violet"
  | "orange"
  | "red"
  | "legendary";

const TAG_PREFIX_COLORS: Array<[string, string]> = [
  ["algorithm/transform", "transform"],
  ["algorithm/string", "string"],
  ["algorithm/graph", "graph"],
  ["algorithm/dp", "dp"],
  ["data-structure", "ds"],
  ["implementation", "implementation"],
  ["paradigm", "paradigm"],
  ["math", "math"],
  ["topic", "topic"],
  ["trick", "trick"],
  ["algorithm", "algorithm"]
];

export function ratingBand(rating: number | null, status: RatingStatus): RatingBand {
  if (rating === null || status !== "official") return "unrated";
  if (rating < 1400) return "gray";
  if (rating < 1600) return "cyan";
  if (rating < 1900) return "blue";
  if (rating < 2100) return "violet";
  if (rating < 2400) return "orange";
  if (rating < 3000) return "red";
  return "legendary";
}

export function ratingClassName(rating: number | null, status: RatingStatus): string {
  return `rating-badge rating-${ratingBand(rating, status)}`;
}

export function tagColorKey(tag: string): string {
  const normalized = tag.toLowerCase();
  const match = TAG_PREFIX_COLORS.find(([prefix]) => normalized.startsWith(prefix));
  return match?.[1] ?? "fallback";
}

export function tagTokenClassName(tag: string, extraClass = ""): string {
  return ["tag-token", `tag-color-${tagColorKey(tag)}`, extraClass]
    .filter(Boolean)
    .join(" ");
}
