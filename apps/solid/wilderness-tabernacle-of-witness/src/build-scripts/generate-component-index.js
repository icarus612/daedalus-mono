import fs from 'fs'
import path from 'path'

const generateComponentIndex = () => {
  const componentsDir = 'src/components'
  const indexFile = path.join(componentsDir, 'index.js')

  let exportStatements = ''

  fs.readdirSync(componentsDir).forEach(file => {
    if (file.endsWith('.jsx')) {
      let componentName = file.replace('.jsx', '')
      componentName = componentName.split('-').map((c)=> c.charAt(0).toUpperCase() + c.slice(1)).join('')
      exportStatements += `export { default as ${componentName} } from './${file}';\n`
    }
  })

  fs.writeFileSync(indexFile, exportStatements)
}

export default generateComponentIndex