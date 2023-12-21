import {useState, useEffect, useRef} from 'react'
import cx from 'classnames'
import Header from 'sections/header'
import Top from 'sections/top'
import Middle from 'sections/middle'
import Bottom from 'sections/bottom'

export default () => {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const w = () => setWidth(window.innerWidth)
    w()
    window.addEventListener('resize', w)
    return () => window.removeEventListener('resize', w)
	}, [width])
	
  return (
    <>
      <Header width={width} />
      <Top width={width} />
      <Middle width={width} />
      <Bottom width={width} />
    </>
  )
}
