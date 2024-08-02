import fs from 'fs'
import path from 'path'

const generateBuildIndex = () => {
  const readDir = 'src/lib/build-scripts'
  const indexFile = path.join(readDir, 'index.js')
  
  let exportStatements = ''
  let functionCalls = ''

  fs.readdirSync(readDir).forEach(file => {
    if (file.endsWith('.js') && file !== 'index.js') {
      let funcName = file.replace('.js', '')
      funcName = funcName.split('-').map((c)=> c.charAt(0).toUpperCase() + c.slice(1)).join('')
      funcName = funcName.charAt(0).toLowerCase() + funcName.slice(1)
      exportStatements += `import ${funcName} from './${file}';\n`
      functionCalls += `${funcName}()\n`
    }
  })
  const fullContent = exportStatements + '\n' + functionCalls
  if (fs.readFileSync(indexFile, 'utf8') !== fullContent) {
    fs.writeFileSync(indexFile, fullContent)
  }
}

export default generateBuildIndex