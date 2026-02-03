"use client";

interface ActorBadgeProps {
  handle: string;
  displayName: string;
  actorType: string;
  isVerified?: boolean;
  postedViaHumanAssist?: boolean;
  size?: "sm" | "md";
}

const typeColors: Record<string, string> = {
  human: "bg-[var(--cg-human)]/20 text-[var(--cg-human)]",
  agent: "bg-[var(--cg-agent)]/20 text-[var(--cg-agent)]",
  council: "bg-[var(--cg-council)]/20 text-[var(--cg-council)]",
};

const typeLabels: Record<string, string> = {
  human: "H",
  agent: "A",
  council: "C",
};

export default function ActorBadge({
  handle,
  displayName,
  actorType,
  isVerified,
  postedViaHumanAssist,
  size = "md",
}: ActorBadgeProps) {
  const iconSize = size === "sm" ? "h-5 w-5 text-xs leading-5" : "h-6 w-6 text-sm leading-6";

  return (
    <a href={`/u/${handle}`} className="flex items-center gap-2 group">
      <span
        className={`inline-block rounded-full text-center font-medium ${iconSize} ${typeColors[actorType] || typeColors.human}`}
      >
        {typeLabels[actorType] || "?"}
      </span>
      <span className="font-medium group-hover:text-[var(--cg-accent)] transition-colors">
        {displayName}
      </span>
      {actorType === "council" && (
        <span className="text-xs text-[var(--cg-council)]">(Council)</span>
      )}
      {postedViaHumanAssist && (
        <span className="text-xs text-[var(--cg-text-muted)] italic">via human assist</span>
      )}
    </a>
  );
}
