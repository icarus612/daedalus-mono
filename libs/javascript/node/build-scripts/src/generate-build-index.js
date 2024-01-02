import fs from 'fs'
import path from 'path'

const generateBuildIndex = () => {
  const indexFile = path.join(componentsDir, 'index.js')

  let exportStatements = ''
  let functionCalls = ''

  fs.readdirSync(componentsDir).forEach(file => {
    if (file.endsWith('.svelte')) {
      let componentName = file.replace('.svelte', '')
      componentName = componentName.split('-').map((c)=> c.charAt(0).toUpperCase() + c.slice(1)).join('')
      exportStatements += `import ${componentName} from './${file}';\n`
      functionCalls += `${componentName}()\n`
    }
  })

  fs.writeFileSync(indexFile, exportStatements)
  fs.writeFileSync(indexFile, functionCalls)
}

export default generateBuildIndex