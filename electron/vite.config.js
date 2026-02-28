import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
    plugins: [react()],
    root: path.join(__dirname, 'renderer'),
    build: {
        outDir: path.join(__dirname, 'renderer/dist'),
        emptyOutDir: true,
    },
})
