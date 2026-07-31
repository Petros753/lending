type StatBlockProps = {
  value: string
  label: string
  /** Direction the hairline divider tilts. */
  tilt?: 'left' | 'right'
  /** Divider above the number instead of below it. */
  dividerPosition?: 'top' | 'bottom'
  align?: 'left' | 'right' | 'center'
  className?: string
}

const alignments = {
  left: 'items-start text-left',
  right: 'items-end text-right',
  center: 'items-center text-center',
}

function Divider({ tilt }: { tilt: 'left' | 'right' }) {
  return (
    <span
      aria-hidden="true"
      className="block h-px w-[60px] bg-white/30"
      style={{ transform: `rotate(${tilt === 'left' ? -20 : 20}deg)` }}
    />
  )
}

export default function StatBlock({
  value,
  label,
  tilt = 'right',
  dividerPosition = 'bottom',
  align = 'left',
  className = '',
}: StatBlockProps) {
  return (
    <div className={`flex flex-col gap-3 ${alignments[align]} ${className}`}>
      {dividerPosition === 'top' && <Divider tilt={tilt} />}
      <div className="text-4xl font-medium leading-none text-[#eeeeee] md:text-5xl">
        {value}
      </div>
      <div className="text-xs text-white/60">{label}</div>
      {dividerPosition === 'bottom' && <Divider tilt={tilt} />}
    </div>
  )
}
