export function DemoVideo() {
  return (
    <video
      className="demoVideo"
      controls
      muted
      playsInline
      preload="metadata"
      poster="/demo-poster.jpg"
      width={3582}
      height={2144}
      aria-label="KortingZoeker budget planning demo — silent, with English captions"
    >
      <source src="/korting_zoeker_demo_001_captioned.mp4" type="video/mp4" />
      <a href="/korting_zoeker_demo_001_captioned.mp4">Watch the captioned demo</a>
    </video>
  );
}
