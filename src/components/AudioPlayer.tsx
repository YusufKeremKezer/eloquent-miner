import { getMediaUrl } from '../api/client';

interface Props {
  filename: string;
}

export default function AudioPlayer({ filename }: Props) {
  const url = getMediaUrl(filename);

  return (
    <audio controls className="w-full h-10" preload="none">
      <source src={url} type="audio/mpeg" />
      Your browser does not support the audio element.
    </audio>
  );
}