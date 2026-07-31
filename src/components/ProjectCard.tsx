import { useState } from 'react'
import {
  motion,
  useReducedMotion,
  useTransform,
  type MotionValue,
} from 'framer-motion'
import type { Project } from '../data/site'

/**
 * Sticky offsets grow with the card index so the stack shows a sliver of every
 * card underneath. Capped so a long list does not push the last cards off screen.
 */
const TOP_BASE = 96
const TOP_STEP = 24
const TOP_MAX = 144

/** Depth of the shrink applied to a card once the next one covers it. */
const SCALE_STEP = 0.03
const MAX_SCALE_STEPS = 5

export function stickyTop(index: number) {
  return Math.min(TOP_BASE + index * TOP_STEP, TOP_MAX)
}

export function targetScale(index: number, total: number) {
  return 1 - Math.min(total - 1 - index, MAX_SCALE_STEPS) * SCALE_STEP
}

type ProjectCardProps = {
  project: Project
  index: number
  total: number
  progress: MotionValue<number>
  /** Sticky stacking is desktop-only; mobile renders a plain vertical list. */
  stacked: boolean
}

function ImagePanel({ project }: { project: Project }) {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <div className="flex aspect-video w-full items-end rounded-2xl bg-gradient-to-br from-white/[0.07] to-white/[0.02] p-5 ring-1 ring-inset ring-white/10">
        <span className="font-mono text-xs uppercase tracking-wide text-white/35">
          {project.category}
        </span>
      </div>
    )
  }

  return (
    <img
      src={import.meta.env.BASE_URL + project.image}
      alt={project.imageAlt}
      loading="lazy"
      decoding="async"
      onError={() => setFailed(true)}
      className="aspect-video w-full rounded-2xl object-cover ring-1 ring-inset ring-white/10"
    />
  )
}

export default function ProjectCard({
  project,
  index,
  total,
  progress,
  stacked,
}: ProjectCardProps) {
  const reduced = useReducedMotion()
  const scale = useTransform(
    progress,
    [index / total, 1],
    [1, targetScale(index, total)],
  )

  return (
    <div
      className={
        stacked
          ? 'sticky top-0 flex h-[78vh] min-h-[720px] items-start justify-center'
          : 'mb-6'
      }
    >
      <motion.article
        initial={stacked || reduced ? undefined : { opacity: 0, y: 24 }}
        whileInView={stacked || reduced ? undefined : { opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '50px' }}
        transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
        style={
          stacked
            ? {
                scale: reduced ? 1 : scale,
                top: stickyTop(index),
                transformOrigin: 'top center',
              }
            : undefined
        }
        className="relative w-full max-w-4xl overflow-hidden rounded-[32px] border border-white/10 bg-surface p-6 md:p-10"
      >
        <div className="grid gap-6 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:gap-10">
          <div>
            <p className="text-xs uppercase tracking-wide text-accent">
              {project.category}
            </p>
            <h3 className="mt-2 text-xl font-medium text-white md:text-2xl">
              {project.title}
            </h3>
            <p className="mt-4 text-sm leading-relaxed text-white/65 md:text-base">
              {project.description}
              {project.highlight && (
                <>
                  {' '}
                  <strong className="font-medium text-accent">
                    {project.highlight}
                  </strong>
                </>
              )}
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {project.stack.map((tech) => (
                <span
                  key={tech}
                  className="rounded-full bg-white/5 px-3 py-1 text-xs text-white/50"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          <ImagePanel project={project} />
        </div>
      </motion.article>
    </div>
  )
}
