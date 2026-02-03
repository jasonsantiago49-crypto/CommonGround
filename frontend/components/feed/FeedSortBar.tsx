"use client";

interface FeedSortBarProps {
  sort: string;
  onSortChange: (sort: string) => void;
}

const sorts = [
  { value: "hot", label: "Hot" },
  { value: "new", label: "New" },
  { value: "top", label: "Top" },
  { value: "rising", label: "Rising" },
];

export default function FeedSortBar({ sort, onSortChange }: FeedSortBarProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-[var(--cg-border)] bg-[var(--cg-surface)] p-1">
      {sorts.map((s) => (
        <button
          key={s.value}
          onClick={() => onSortChange(s.value)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            sort === s.value
              ? "bg-[var(--cg-accent)] text-white"
              : "text-[var(--cg-text-muted)] hover:text-[var(--cg-text)] hover:bg-[var(--cg-surface-hover)]"
          }`}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
