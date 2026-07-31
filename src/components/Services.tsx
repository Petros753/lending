import FadeIn from './FadeIn'
import { services } from '../data/site'

export default function Services() {
  return (
    <section id="services" className="scroll-mt-28 bg-[#0a0a0a] px-6 py-24 md:px-10">
      <div className="mx-auto max-w-4xl">
        <FadeIn>
          <h2
            className="font-medium text-white"
            style={{ fontSize: 'clamp(2rem, 6vw, 3.5rem)', letterSpacing: '-0.02em' }}
          >
            Что я делаю
          </h2>
          <p className="mt-4 max-w-xl text-white/60">
            Создаю автоматизации любой сложности — от простых интеграций до
            комплексных AI-систем
          </p>
        </FadeIn>

        <ul className="mt-16">
          {services.map((service, index) => (
            <li key={service.number}>
              <FadeIn delay={index * 0.08} y={20}>
                <div className="flex flex-col gap-4 border-b border-white/10 py-8 sm:flex-row sm:gap-8">
                  <span
                    aria-hidden="true"
                    className="font-bold leading-none text-white/15"
                    style={{ fontSize: 'clamp(2.5rem, 7vw, 5rem)' }}
                  >
                    {service.number}
                  </span>

                  <div className="flex-1 pt-1">
                    <h3 className="text-xl font-medium text-white md:text-2xl">
                      {service.title}
                    </h3>
                    <p className="mt-2 max-w-xl leading-relaxed text-white/65">
                      {service.description}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {service.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-white/5 px-3 py-1 font-mono text-xs text-white/50"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </FadeIn>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
