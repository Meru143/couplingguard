import { Composition } from "remotion";
import { CouplingDemo } from "./CouplingDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CouplingDemo"
      component={CouplingDemo}
      durationInFrames={30 * 24} // 24 seconds at 30 fps
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
