import fs from 'fs'

const generateComponentIndex = () => {
  const imagesDir = 'images/fullrez/'
  const componentsDir = 'static/'+ imagesDir
  const indexFile = 'src/lib/static-exports/images.js'
  let exportItems = 'export default [\n'

  fs.readdirSync(componentsDir).forEach((file) => {
    exportItems += `\t'${imagesDir}/${file}',\n`
  })
  exportItems += ']'
  if (fs.readFileSync(indexFile, 'utf8') !== exportItems) {
    fs.writeFileSync(indexFile, exportItems)
  }
}

export default generateComponentIndex