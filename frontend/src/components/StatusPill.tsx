export default function StatusPill(props: { ok: boolean; text: string }) {
  return <span className={`pill ${props.ok ? "pillOk" : "pillBad"}`}>{props.text}</span>;
}

