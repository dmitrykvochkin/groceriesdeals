type BrandMarkProps = {
  className?: string;
};

/** SVG mark matching the site brandMark (purple tile + three dots). */
export function BrandMark({ className = "brandMark" }: BrandMarkProps) {
  return (
    <svg className={className} viewBox="0 0 34 34" aria-hidden="true">
      <path
        fill="currentColor"
        d="M10 0h14a10 10 0 0 1 10 10v14a10 10 0 0 1-10 10H3a3 3 0 0 1-3-3V10A10 10 0 0 1 10 0Z"
      />
      <circle cx="10" cy="15" r="2.5" fill="#fff" />
      <circle cx="24" cy="15" r="2.5" fill="#fff" />
      <circle cx="17" cy="22" r="2.5" fill="#fff" />
    </svg>
  );
}
