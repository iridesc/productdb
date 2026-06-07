import { showImagePreview } from 'vant'

export function previewImage(url: string) {
  showImagePreview({
    images: [url],
    closeable: true,
    closeIcon: 'clear',
    showIndex: false,
  })
}

export function previewImages(urls: string[], startIndex: number = 0) {
  showImagePreview({
    images: urls,
    startPosition: startIndex,
    closeable: true,
    closeIcon: 'clear',
  })
}
