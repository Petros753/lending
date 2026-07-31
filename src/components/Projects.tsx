import { useRef } from 'react'
import { useScroll } from 'framer-motion'
import FadeIn from './FadeIn'
import ProjectCard from './ProjectCard'
import useMediaQuery from '../hooks/useMediaQuery'
import { projects } from '../data/site'

export default function Projects() {
  const containerRef = useRef<HTMLDivElement>(null)
  // Sticky stacking only from lg up. Below that the card switches to a stacked
  // single-column layout that is too tall to pin without clipping, so the cards
  // scroll as an ordinary list instead.
  const stacked = useMediaQuery('(min-width: 1024px)')

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  return (
    <section id="projects" className="scroll-mt-28 px-6 py-24 md:px-10">
      <div className="mx-auto max-w-4xl">
        <FadeIn>
          <h2
            className="font-medium text-white"
            style={{ fontSize: 'clamp(2rem, 6vw, 3.5rem)', letterSpacing: '-0.02em' }}
          >
            Избранные проекты
          </h2>
          <p className="mt-4 text-white/60">
            Реальные кейсы автоматизации для бизнеса
          </p>
        </FadeIn>
      </div>

      <div ref={containerRef} className="mt-16">
        {projects.map((project, index) => (
          <ProjectCard
            key={project.title}
            project={project}
            index={index}
            total={projects.length}
            progress={scrollYProgress}
            stacked={stacked}
          />
        ))}
      </div>
    </section>
  )
}
