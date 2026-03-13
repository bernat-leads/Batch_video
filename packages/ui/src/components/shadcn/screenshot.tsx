interface ScreenshotProps {
  srcLight: string;
  srcDark?: string;
  alt: string;
  width: number;
  height: number;
  className?: string;
}

export default function Screenshot({ srcLight, alt, width, height, className }: ScreenshotProps) {
  // For Astro, we'll use the light image by default
  // In a real implementation, you might want to handle theme switching differently
  const src = srcLight;

  return <img src={src} alt={alt} width={width} height={height} className={className} />;
}
