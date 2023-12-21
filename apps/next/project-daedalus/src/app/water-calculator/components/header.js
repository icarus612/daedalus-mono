import React from 'react';
import cx from "classnames"
import Image from 'components/image'

import local from 'styles/sections/header.module.scss'
import layout from 'styles/layout.module.scss'

import Link from "next/link"

export default ()=> {
    return (
        <nav className={cx(local.nav_bar, layout.f_row, layout.justify_end, layout.align_center)}>

          <div className={cx(layout.f_row, layout.justify_center, layout.align_center)}>
            <Link href="/residential">residential</Link>
						<div className={local.divider}>|</div>
            <Link href="/commercial">commercial</Link>
						<div className={local.divider}>|</div>
						<Link href="/info">info</Link>
            <div className={local.divider}>|</div>
          </div>
          <Link href="https://devicarus.com">
            <Image className={local.logo} src="images/devicarus.png" />
          </Link>
        </nav>
       
    )
}
