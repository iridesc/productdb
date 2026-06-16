import { showImagePreview } from 'vant'

export function previewImage(url: string) {
  const instance = showImagePreview({
    images: [url],
    closeable: true,
    closeIcon: 'clear',
    showIndex: false,
    closeOnPopstate: true,
  } as any)
  // 点击图片关闭预览
  setTimeout(() => {
    const swipe = document.querySelector('.van-image-preview__swipe')
    if (swipe) {
      swipe.addEventListener('click', () => instance.close())
    }
  }, 100)
}

export function previewImages(urls: string[], startIndex: number = 0) {
  const instance = showImagePreview({
    images: urls,
    startPosition: startIndex,
    closeable: true,
    closeIcon: 'clear',
    closeOnPopstate: true,
  } as any)
  // 点击图片关闭预览
  setTimeout(() => {
    const swipe = document.querySelector('.van-image-preview__swipe')
    if (swipe) {
      swipe.addEventListener('click', () => instance.close())
    }
  }, 100)
}
