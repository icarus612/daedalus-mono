import { useState, useEffect, useRef } from 'react'
import cx from 'classnames'
import { useRouter } from 'next/router'
import local from 'styles/components/image.module.scss'

export default (props) => {
	const {
		className,
		alt,
		src,
		width,
		height,
		layout,
		onLoad = () => null,
		onClick = () => null,
		objectPosition,
	} = props

	const router = useRouter()
	const [currentPath, setCurrentPath] = useState(false)
	const imgRef = useRef(null)
	const loaded = () => {
		imgRef.current && (imgRef.current.classList.add(local.loaded))
		onLoad()
	}

	useEffect(()=> currentPath === router.pathname ? loaded() : setCurrentPath(router.pathname))

  return (
		<img 
			className={cx(className, local.image, local[layout === "fill" && "fill"])}
			alt={alt}
			src={src}
			width={width}
			height={height}
			ref={imgRef}
			onClick={(e)=> onClick(e)}
			onLoad={()=> loaded()}
			style={{objectPosition}}
		/>
  )
}
