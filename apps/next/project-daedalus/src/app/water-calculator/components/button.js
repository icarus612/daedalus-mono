import React, {useState} from 'react'

const Button = (props) => {
  const [selectValue, setSelectValue] = useState(props.options && props.options[0])
  const {className='basic'} = props
  const classes = `btn ${typeof className == 'string' ? className : className.join(' ')}`
  if (props.type === "select"){
    const onChange = (e) => {
      setSelectValue(e)
      if (props.onChange) return props.onChange(e)
    }
    return (<select 
      className={classes} 
      name={props.name} 
      id={props.name} 
      value={selectValue} 
      onChange={(e)=> onChange(e.target.value)}
    >
      { props.options ? props.options.map((i)=> <option value={i} key={i}>{i}</option>) : ""}
    </select>)
   } else {
    return (
      <button 
        className={classes}
        onClick={props.onClick}
        type={props.type ? props.type : 'button'} 
      >
        {props.value}
      </button>
    )
  }
}

export default Button