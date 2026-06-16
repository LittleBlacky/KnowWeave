export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "warning" | "danger" | "accent";
}) {
  const toneClass = {
    neutral: "border-[#dcded8] text-[#6f756f] bg-white",
    warning: "border-[#e6d5b3] text-[#9a5a13] bg-[#fef9ef]",
    danger: "border-[#e8c8c5] text-[#a23b35] bg-[#fdf4f3]",
    accent: "border-[#b8d4cd] text-[#123d37] bg-[#e1ebe7]",
  }[tone];

  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${toneClass}`}>
      {children}
    </span>
  );
}
