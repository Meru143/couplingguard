import {
  AbsoluteFill,
  Sequence,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, FONTS } from "./theme";

/**
 * 24-second product demo for couplingguard.
 *
 * Timeline (fps=30, total 720 frames):
 *   0.0–3.0s  Title card: "couplingguard"
 *   3.0–8.0s  The pain: a PR comment that should have happened
 *   8.0–14.0s The fix: data flow git log → matrix → score
 *   14.0–20.0s Rendered PR comment with risk badges + delta
 *   20.0–24.0s CTA: install in 5 lines
 *
 * No CSS transitions or @keyframes (forbidden in Remotion).
 * All motion uses useCurrentFrame() + interpolate().
 */

const fadeIn = (frame: number, start: number, dur = 15) =>
  interpolate(frame, [start, start + dur], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const slideY = (frame: number, start: number, dur = 18) =>
  interpolate(frame, [start, start + dur], [40, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const Background: React.FC = () => (
  <AbsoluteFill
    style={{
      background: `linear-gradient(135deg, ${COLORS.bgFrom} 0%, ${COLORS.bgTo} 100%)`,
    }}
  />
);

const SceneTitle: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        fontFamily: FONTS.sans,
        color: COLORS.fg,
      }}
    >
      <div
        style={{
          opacity: fadeIn(frame, 0),
          transform: `translateY(${slideY(frame, 0)}px)`,
          fontSize: 180,
          fontWeight: 800,
          letterSpacing: -6,
        }}
      >
        coupling<span style={{ color: COLORS.accent }}>guard</span>
      </div>
      <div
        style={{
          marginTop: 24,
          opacity: fadeIn(frame, 20),
          transform: `translateY(${slideY(frame, 20)}px)`,
          fontSize: 44,
          color: COLORS.fgDim,
          fontWeight: 500,
          maxWidth: 1400,
        }}
      >
        Detect file coupling risk in PRs from git co-change history.
      </div>
      <div
        style={{
          marginTop: 20,
          opacity: fadeIn(frame, 40),
          fontSize: 28,
          color: COLORS.fgFaint,
          fontFamily: FONTS.mono,
        }}
      >
        Free · Zero-config · 5 lines of YAML
      </div>
    </AbsoluteFill>
  );
};

const ScenePain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: FONTS.sans,
        color: COLORS.fg,
        padding: 120,
      }}
    >
      <div
        style={{
          fontSize: 72,
          fontWeight: 800,
          opacity: fadeIn(frame, 0),
          transform: `translateY(${slideY(frame, 0)}px)`,
          marginBottom: 40,
          maxWidth: 1500,
          textAlign: "center",
        }}
      >
        Two files always break together.
      </div>
      <div
        style={{
          fontSize: 48,
          color: COLORS.fgDim,
          opacity: fadeIn(frame, 25),
          transform: `translateY(${slideY(frame, 25)}px)`,
          maxWidth: 1500,
          textAlign: "center",
          marginBottom: 60,
        }}
      >
        Your git log knows. Nobody's reading it.
      </div>

      {/* Three example commits */}
      <div style={{ display: "flex", flexDirection: "column", gap: 18, fontFamily: FONTS.mono, fontSize: 28 }}>
        {[
          { sha: "a3f9c2", files: "src/payment.py + src/billing.py", delay: 50 },
          { sha: "b1d8e3", files: "src/payment.py + tests/test_billing.py", delay: 65 },
          { sha: "c92ef0", files: "src/payment.py + src/billing.py", delay: 80 },
        ].map((c) => (
          <div
            key={c.sha}
            style={{
              opacity: fadeIn(frame, c.delay),
              transform: `translateY(${slideY(frame, c.delay)}px)`,
              padding: "14px 28px",
              borderRadius: 10,
              background: COLORS.card,
              border: `1px solid ${COLORS.cardStroke}`,
              color: COLORS.fgDim,
              minWidth: 760,
            }}
          >
            <span style={{ color: COLORS.fgFaint }}>{c.sha}  </span>
            {c.files}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const SceneFormula: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: FONTS.sans,
        color: COLORS.fg,
        padding: 120,
        textAlign: "center",
      }}
    >
      <div
        style={{
          fontSize: 36,
          color: COLORS.fgMute,
          letterSpacing: 6,
          opacity: fadeIn(frame, 0),
          transform: `translateY(${slideY(frame, 0)}px)`,
          marginBottom: 28,
        }}
      >
        NORMALIZED COUPLING SCORE
      </div>
      <div
        style={{
          fontFamily: FONTS.mono,
          fontSize: 86,
          color: COLORS.fg,
          opacity: fadeIn(frame, 20),
          transform: `translateY(${slideY(frame, 20)}px)`,
          marginBottom: 60,
          background: COLORS.card,
          border: `1px solid ${COLORS.cardStroke}`,
          padding: "36px 60px",
          borderRadius: 16,
        }}
      >
        score = <span style={{ color: COLORS.accent }}>co_changes</span>
        {" / "}max(count<sub>a</sub>, count<sub>b</sub>)
      </div>

      <div
        style={{
          fontSize: 36,
          color: COLORS.fgDim,
          maxWidth: 1500,
          lineHeight: 1.4,
          opacity: fadeIn(frame, 50),
        }}
      >
        A 0–1 ratio that's comparable across repos of any size and age.
      </div>
    </AbsoluteFill>
  );
};

const PRRow: React.FC<{
  file: string;
  coupled: string;
  score: number;
  riskEmoji: string;
  riskLabel: string;
  riskColor: string;
  coChanges: string;
  delay: number;
}> = ({ file, coupled, score, riskEmoji, riskLabel, riskColor, coChanges, delay }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.4fr 1.4fr 0.6fr 0.9fr 0.9fr",
        gap: 24,
        alignItems: "center",
        padding: "20px 32px",
        borderBottom: `1px solid ${COLORS.prCardStroke}`,
        fontFamily: FONTS.mono,
        fontSize: 26,
        opacity: fadeIn(frame, delay),
        transform: `translateY(${slideY(frame, delay)}px)`,
      }}
    >
      <span style={{ color: COLORS.prFg }}>{file}</span>
      <span style={{ color: COLORS.prFg }}>{coupled}</span>
      <span style={{ color: riskColor, fontWeight: 700 }}>{score.toFixed(2)}</span>
      <span style={{ color: riskColor, fontWeight: 600 }}>{riskEmoji} {riskLabel}</span>
      <span style={{ color: COLORS.prFgDim }}>{coChanges}</span>
    </div>
  );
};

const SceneComment: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: FONTS.sans,
        padding: 80,
      }}
    >
      <div
        style={{
          width: 1500,
          background: COLORS.prCard,
          border: `2px solid ${COLORS.prCardStroke}`,
          borderRadius: 16,
          boxShadow: "0 30px 60px rgba(0,0,0,0.45)",
          opacity: fadeIn(frame, 0),
          transform: `translateY(${slideY(frame, 0)}px)`,
        }}
      >
        {/* PR comment header */}
        <div
          style={{
            padding: "32px 40px",
            borderBottom: `1px solid ${COLORS.prCardStroke}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ color: COLORS.prFg, fontSize: 34, fontWeight: 700 }}>
              🔍 couplingguard
            </div>
            <div style={{ color: COLORS.prFgDim, fontSize: 22, marginTop: 6 }}>
              2 pairs detected, highest risk:
            </div>
          </div>
          <div
            style={{
              color: COLORS.riskHigh,
              fontSize: 64,
              fontWeight: 800,
              fontFamily: FONTS.sans,
              opacity: fadeIn(frame, 12),
            }}
          >
            🔴 0.82
          </div>
        </div>

        {/* Table headers */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.4fr 1.4fr 0.6fr 0.9fr 0.9fr",
            gap: 24,
            padding: "16px 32px",
            color: COLORS.prFgDim,
            fontFamily: FONTS.mono,
            fontSize: 22,
            borderBottom: `1px solid ${COLORS.prCardStroke}`,
          }}
        >
          <span>File in PR</span>
          <span>Coupled with</span>
          <span>Score</span>
          <span>Risk</span>
          <span>Co-changes</span>
        </div>

        {/* Rows */}
        <PRRow
          file="payment.py"
          coupled="billing.py"
          score={0.82}
          riskEmoji="🔴"
          riskLabel="High"
          riskColor={COLORS.riskHigh}
          coChanges="41/50 commits"
          delay={24}
        />
        <PRRow
          file="payment.py"
          coupled="tests/test_billing.py"
          score={0.64}
          riskEmoji="🟡"
          riskLabel="Medium"
          riskColor={COLORS.riskMid}
          coChanges="32/50 commits"
          delay={36}
        />

        {/* Delta line */}
        <div
          style={{
            margin: "28px 32px",
            padding: "20px 24px",
            background: "#1f2937",
            border: `1px solid ${COLORS.riskMid}80`,
            borderRadius: 10,
            opacity: fadeIn(frame, 60),
            transform: `translateY(${slideY(frame, 60)}px)`,
          }}
        >
          <div style={{ color: COLORS.prFg, fontSize: 24, marginBottom: 6 }}>
            ⚠️ Score changed since last push:
          </div>
          <div style={{ color: COLORS.riskMid, fontFamily: FONTS.mono, fontSize: 30, fontWeight: 700 }}>
            🟡 0.45 → 🔴 0.82 ↑
          </div>
        </div>

        {/* Reviewers */}
        <div
          style={{
            padding: "0 32px 32px",
            opacity: fadeIn(frame, 80),
          }}
        >
          <div style={{ color: COLORS.prFgDim, fontSize: 22, marginBottom: 8 }}>
            Suggested reviewers (via CODEOWNERS):
          </div>
          <div style={{ color: COLORS.link, fontFamily: FONTS.mono, fontSize: 26 }}>
            @alice  @team-payments
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const SceneCTA: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: FONTS.sans,
        textAlign: "center",
        padding: 120,
      }}
    >
      <div
        style={{
          fontSize: 72,
          fontWeight: 800,
          color: COLORS.fg,
          opacity: fadeIn(frame, 0),
          transform: `translateY(${slideY(frame, 0)}px)`,
          marginBottom: 32,
        }}
      >
        Install in 5 lines.
      </div>

      <pre
        style={{
          fontFamily: FONTS.mono,
          fontSize: 28,
          background: COLORS.card,
          border: `1px solid ${COLORS.cardStroke}`,
          borderRadius: 14,
          padding: "32px 40px",
          color: COLORS.fgDim,
          textAlign: "left",
          opacity: fadeIn(frame, 20),
          transform: `translateY(${slideY(frame, 20)}px)`,
        }}
      >
        <span style={{ color: COLORS.fgMute }}>{`- uses: actions/checkout@v4
  with:
    fetch-depth: 0
`}</span>
        <span style={{ color: COLORS.accent }}>{`- uses: Meru143/couplingguard@v1`}</span>
      </pre>

      <div
        style={{
          marginTop: 40,
          fontSize: 32,
          color: COLORS.fgMute,
          opacity: fadeIn(frame, 50),
          fontFamily: FONTS.mono,
        }}
      >
        github.com/Meru143/couplingguard
      </div>
    </AbsoluteFill>
  );
};

export const CouplingDemo: React.FC = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Background />

      {/* 0.0–3.0s */}
      <Sequence durationInFrames={3 * fps}>
        <SceneTitle />
      </Sequence>

      {/* 3.0–8.0s */}
      <Sequence from={3 * fps} durationInFrames={5 * fps}>
        <ScenePain />
      </Sequence>

      {/* 8.0–14.0s */}
      <Sequence from={8 * fps} durationInFrames={6 * fps}>
        <SceneFormula />
      </Sequence>

      {/* 14.0–20.0s */}
      <Sequence from={14 * fps} durationInFrames={6 * fps}>
        <SceneComment />
      </Sequence>

      {/* 20.0–24.0s */}
      <Sequence from={20 * fps} durationInFrames={4 * fps}>
        <SceneCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
