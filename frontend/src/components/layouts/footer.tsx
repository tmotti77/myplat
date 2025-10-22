import { useTranslation } from 'next-i18next'
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  Brain,
  Mail,
  Phone,
  MapPin,
  Github,
  Twitter,
  Linkedin,
  Youtube,
  Facebook,
  Instagram,
  Globe,
  Shield,
  FileText,
  HelpCircle,
  Users,
  Zap,
  Award,
  Heart,
  ExternalLink,
  ChevronUp,
  Languages,
  Accessibility,
  Eye,
  Volume2,
  Type,
  Contrast,
  MousePointer,
  Keyboard,
  Focus,
  ArrowUp
} from 'lucide-react'
import { useState, useEffect } from 'react'

// Hooks
import { useRTL } from '@/components/providers/rtl-provider'
import { useTheme } from '@/components/providers/theme-provider'
import { useAccessibility } from '@/components/providers/accessibility-provider'

// Utils
import { cn } from '@/lib/utils'

interface FooterProps {
  className?: string
  minimal?: boolean
}

interface FooterLink {
  label: string
  href: string
  external?: boolean
  icon?: React.ComponentType<{ className?: string }>
}

interface FooterSection {
  title: string
  links: FooterLink[]
}

export function Footer({ className, minimal = false }: FooterProps) {
  const { t } = useTranslation(['footer', 'common', 'navigation'])
  const router = useRouter()
  const { direction } = useRTL()
  const { theme } = useTheme()
  const { announceAction } = useAccessibility()
  
  const [showBackToTop, setShowBackToTop] = useState(false)
  const [currentYear] = useState(new Date().getFullYear())

  // Show back to top button when scrolled
  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > 400)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const footerSections: FooterSection[] = [
    {
      title: t('footer:product'),
      links: [
        { label: t('footer:features'), href: '/features' },
        { label: t('footer:pricing'), href: '/pricing' },
        { label: t('footer:security'), href: '/security', icon: Shield },
        { label: t('footer:integrations'), href: '/integrations' },
        { label: t('footer:apiDocs'), href: '/docs/api', icon: FileText },
        { label: t('footer:changelog'), href: '/changelog' }
      ]
    },
    {
      title: t('footer:solutions'),
      links: [
        { label: t('footer:enterprise'), href: '/enterprise' },
        { label: t('footer:teams'), href: '/teams', icon: Users },
        { label: t('footer:education'), href: '/education' },
        { label: t('footer:healthcare'), href: '/healthcare' },
        { label: t('footer:legal'), href: '/legal' },
        { label: t('footer:consulting'), href: '/consulting' }
      ]
    },
    {
      title: t('footer:resources'),
      links: [
        { label: t('footer:documentation'), href: '/docs', icon: FileText },
        { label: t('footer:tutorials'), href: '/tutorials' },
        { label: t('footer:blog'), href: '/blog' },
        { label: t('footer:community'), href: '/community', icon: Users },
        { label: t('footer:support'), href: '/support', icon: HelpCircle },
        { label: t('footer:status'), href: '/status', external: true }
      ]
    },
    {
      title: t('footer:company'),
      links: [
        { label: t('footer:about'), href: '/about' },
        { label: t('footer:careers'), href: '/careers' },
        { label: t('footer:press'), href: '/press' },
        { label: t('footer:investors'), href: '/investors' },
        { label: t('footer:partners'), href: '/partners' },
        { label: t('footer:contact'), href: '/contact', icon: Mail }
      ]
    }
  ]

  const legalLinks: FooterLink[] = [
    { label: t('footer:privacy'), href: '/privacy' },
    { label: t('footer:terms'), href: '/terms' },
    { label: t('footer:cookies'), href: '/cookies' },
    { label: t('footer:gdpr'), href: '/gdpr' },
    { label: t('footer:accessibility'), href: '/accessibility', icon: Accessibility },
    { label: t('footer:licenses'), href: '/licenses' }
  ]

  const socialLinks: FooterLink[] = [
    { label: 'GitHub', href: 'https://github.com/company', external: true, icon: Github },
    { label: 'Twitter', href: 'https://twitter.com/company', external: true, icon: Twitter },
    { label: 'LinkedIn', href: 'https://linkedin.com/company/company', external: true, icon: Linkedin },
    { label: 'YouTube', href: 'https://youtube.com/company', external: true, icon: Youtube }
  ]

  const contactInfo = {
    email: 'hello@myplatform.com',
    phone: '+1 (555) 123-4567',
    address: '123 Tech Street, San Francisco, CA 94105, USA'
  }

  const handleBackToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    announceAction(t('footer:backToTopAction'), 'polite')
  }

  const handleLinkClick = (link: FooterLink) => {
    if (link.external) {
      announceAction(t('footer:externalLinkOpening', { site: link.label }), 'polite')
    } else {
      announceAction(t('footer:navigatingTo', { page: link.label }), 'polite')
    }
  }

  if (minimal) {
    return (
      <footer 
        className={cn(
          'border-t border-border bg-background/95 backdrop-blur mt-auto',
          className
        )}
        dir={direction}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-primary" />
                <span className="font-semibold text-foreground">
                  {t('common:appName')}
                </span>
              </div>
              <span className="text-sm text-muted-foreground">
                © {currentYear}
              </span>
            </div>
            
            <div className="flex items-center space-x-4 text-sm">
              {legalLinks.slice(0, 3).map((link, index) => (
                <Link
                  key={index}
                  href={link.href}
                  className="text-muted-foreground hover:text-foreground transition-colors focus-visible-ring rounded"
                  onClick={() => handleLinkClick(link)}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </footer>
    )
  }

  return (
    <footer 
      className={cn(
        'border-t border-border bg-muted/30 mt-auto',
        className
      )}
      dir={direction}
      role="contentinfo"
      aria-label={t('footer:footerNavigation')}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main footer content */}
        <div className="py-12 lg:py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8 lg:gap-12">
            {/* Brand section */}
            <div className="lg:col-span-2">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                  <Brain className="w-6 h-6 text-primary-foreground" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground">
                    {t('common:appName')}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t('common:tagline')}
                  </p>
                </div>
              </div>
              
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                {t('footer:description')}
              </p>

              {/* Contact info */}
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-3">
                  <Mail className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <a 
                    href={`mailto:${contactInfo.email}`}
                    className="text-muted-foreground hover:text-foreground transition-colors focus-visible-ring rounded"
                  >
                    {contactInfo.email}
                  </a>
                </div>
                <div className="flex items-center space-x-3">
                  <Phone className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <a 
                    href={`tel:${contactInfo.phone}`}
                    className="text-muted-foreground hover:text-foreground transition-colors focus-visible-ring rounded"
                  >
                    {contactInfo.phone}
                  </a>
                </div>
                <div className="flex items-start space-x-3">
                  <MapPin className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                  <span className="text-muted-foreground leading-relaxed">
                    {contactInfo.address}
                  </span>
                </div>
              </div>

              {/* Social links */}
              <div className="flex items-center space-x-4 mt-6">
                {socialLinks.map((social, index) => {
                  const Icon = social.icon!
                  return (
                    <a
                      key={index}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg bg-background hover:bg-accent transition-colors focus-visible-ring"
                      aria-label={t('footer:followOnSocial', { platform: social.label })}
                      onClick={() => handleLinkClick(social)}
                    >
                      <Icon className="w-4 h-4" />
                    </a>
                  )
                })}
              </div>
            </div>

            {/* Footer sections */}
            {footerSections.map((section, sectionIndex) => (
              <div key={sectionIndex} className="lg:col-span-1">
                <h4 className="text-sm font-semibold text-foreground mb-4">
                  {section.title}
                </h4>
                <ul className="space-y-3">
                  {section.links.map((link, linkIndex) => {
                    const Icon = link.icon
                    return (
                      <li key={linkIndex}>
                        <Link
                          href={link.href}
                          className="flex items-center space-x-2 text-sm text-muted-foreground hover:text-foreground transition-colors focus-visible-ring rounded group"
                          target={link.external ? '_blank' : undefined}
                          rel={link.external ? 'noopener noreferrer' : undefined}
                          onClick={() => handleLinkClick(link)}
                        >
                          {Icon && (
                            <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                          )}
                          <span>{link.label}</span>
                          {link.external && (
                            <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          )}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Newsletter signup */}
        <div className="py-8 border-t border-border">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
            <div className="max-w-md">
              <h4 className="text-lg font-semibold text-foreground mb-2">
                {t('footer:newsletter')}
              </h4>
              <p className="text-sm text-muted-foreground">
                {t('footer:newsletterDescription')}
              </p>
            </div>
            
            <form className="flex w-full lg:w-auto max-w-md">
              <input
                type="email"
                placeholder={t('footer:emailPlaceholder')}
                className="flex-1 px-4 py-2 bg-background border border-border rounded-s-lg focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                aria-label={t('footer:emailAddress')}
              />
              <button
                type="submit"
                className="px-6 py-2 bg-primary text-primary-foreground rounded-e-lg hover:bg-primary/90 transition-colors focus-visible-ring"
              >
                {t('footer:subscribe')}
              </button>
            </form>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="py-6 border-t border-border">
          <div className="flex flex-col lg:flex-row justify-between items-center space-y-4 lg:space-y-0">
            {/* Copyright and legal */}
            <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-6">
              <p className="text-sm text-muted-foreground">
                © {currentYear} {t('common:appName')}. {t('footer:allRightsReserved')}
              </p>
              <div className="flex items-center space-x-4">
                {legalLinks.map((link, index) => {
                  const Icon = link.icon
                  return (
                    <Link
                      key={index}
                      href={link.href}
                      className="flex items-center space-x-1 text-sm text-muted-foreground hover:text-foreground transition-colors focus-visible-ring rounded"
                      onClick={() => handleLinkClick(link)}
                    >
                      {Icon && <Icon className="w-3 h-3" />}
                      <span>{link.label}</span>
                    </Link>
                  )
                })}
              </div>
            </div>

            {/* Status indicators */}
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-muted-foreground">
                  {t('footer:allSystemsOperational')}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {router.locale?.toUpperCase() || 'EN'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Accessibility statement */}
        <div className="py-4 border-t border-border">
          <p className="text-xs text-muted-foreground text-center leading-relaxed">
            {t('footer:accessibilityStatement')}{' '}
            <Link 
              href="/accessibility" 
              className="text-primary hover:underline focus-visible-ring rounded"
            >
              {t('footer:learnMore')}
            </Link>
            {'. '}
            {t('footer:wcagCompliance')}
          </p>
        </div>
      </div>

      {/* Back to top button */}
      {showBackToTop && (
        <button
          onClick={handleBackToTop}
          className="fixed bottom-6 end-6 p-3 bg-primary text-primary-foreground rounded-full shadow-lg hover:shadow-xl transition-all focus-visible-ring z-50"
          aria-label={t('footer:backToTop')}
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      )}

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          footer {
            display: none !important;
          }
        }
      `}</style>
    </footer>
  )
}