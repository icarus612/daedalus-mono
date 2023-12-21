import { useState, useEffect, useRef } from 'react'
import cx from 'classnames'
import Link from 'next/link'

import Header from 'sections/header'
import Throbber from 'components/throbber'
import Swoosh from 'components/swoosh'

import { scrollBG } from 'modules/color-changer'

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default () => {
  useEffect(() => scrollBG('body', ["#134a89", "#6D289A", "#1ea185", "#134a89"], 3500))
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const w = () => setWidth(window.innerWidth)
    w()
    window.addEventListener('resize', w)
    return () => window.removeEventListener('resize', w)
	}, [width])
  const firstRef = useRef(null)
  const secondRef = useRef(null)
  const thirdRef = useRef(null)
  const fourthRef = useRef(null)
  const fifthRef = useRef(null)
  const sixthRef = useRef(null)
  return (
    <>
      <Header />
      <div className={cx(layout.container, global.container_margin)}>
        <div className={cx(layout.w100_percent, layout.f_row, layout.justify_center)}>
          <div className={cx(global.card, layout.block_12, layout.text_center)}>
            <h1>
              Quest: A Creative Landing Page Theme For Easy Use
            </h1>
            <p>
              Designed By Project Icarus
            </p>
            <div className={cx(layout.f_row, layout.justify_center)}>
              <Link href="https://github.com/icarus612/questLandingPage">
                <div className={global.btn_purple_basic}>Visit Github</div>
              </Link>
              <Link target='_blank' href="https://www.projecticarus.net">
                <div className={global.btn_purple_basic}>Main Site</div>
              </Link>
            </div>
            <Throbber placement="bottom" ref={firstRef} mobile={width < 600 && "right"} />
          </div>
        </div>

        <Swoosh startElement={firstRef} endElement={secondRef} width={width} />

        <div className={cx(layout.w100_percent, layout.f_row, layout.justify_start)}>
          <div className={cx(global.card, layout.block_12_mob, layout.block_6)}>
            <Throbber placement="top" ref={secondRef} mobile={width < 600 && "left"} />
            <h3>JavaScript</h3>
            <p>
              JavaScript is amazing for so many reasons, and if you don't believe me, look uo "how to disable Javascript in my browser", and play around online for 10-20 minutes. (Most pages wont even let you view them without JS enabled)
            </p>
            <p>
              Most of my pages are made to show off JavaScript animation, that are fun, reactive and interactive with the user.
            </p>
            <Throbber placement="bottom" ref={thirdRef} mobile={width < 600 && "left"} />
          </div>
        </div>

        <Swoosh startElement={thirdRef} endElement={fourthRef} width={width} />

        <div className={cx(layout.w100_percent, layout.f_row, layout.justify_end)}>
          <div className={cx(global.card, layout.block_12_mob, layout.block_6)}>
            <Throbber placement="top" ref={fourthRef} mobile={width < 600 && "right"} />
            <h3>
              Animations with anime.js
            </h3>
            <p>
              This is whats going on behind the scenes with the dots. (to see the dots animation repo <Link target='_blank' href="https://github.com/icarus612/dots">click here</Link>
            </p>
            <p>I'm using a modified version here to dynamically change the distance if the page size changes. (try it out)</p>
            <Throbber placement="bottom" ref={fifthRef} mobile={width < 600 && "right"} />
          </div>
        </div>

        <Swoosh startElement={fifthRef} endElement={sixthRef} width={width} />

        <div className={cx(layout.w100_percent, layout.f_row, layout.justify_start)}>
          <div className={cx(global.card, layout.block_12_mob, layout.block_6)}>
            <Throbber placement="top" ref={sixthRef} mobile={width < 600 && "left"} />
            <h3>
              Use as you wish
            </h3>
            <p>
              This landing page is avalible for download (obviously), and others like it. Check out <Link target='_blank' href='https://devicarus.com'>this page</Link> for more cool js anamations in action.
              The link to either github is here:
            </p>
            <div className={layout.f_row}>
              <Link target='_blank' href="https://github.com/icarus612/quest-next-JS">
                <div className={global.btn_purple_basic}>Quest</div>
              </Link>
              <Link target='_blank' href="https://github.com/icarus612">
                <div className={global.btn_purple_basic}>Github</div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}