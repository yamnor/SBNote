/**
 * スクロール制御機能を提供するコンポーザブル
 * Note.vueとQuickNoteModal.vueで共通のスクロール制御ロジックを提供します
 */
export function useScrollControl() {
  /**
   * 指定されたターゲットの最上部にスクロールする
   * @param {Object} options - スクロールオプション
   * @param {string} options.behavior - スクロール動作 ('auto' | 'smooth')
   * @param {string} options.target - スクロール対象 ('window' | 'modal')
   */
  const scrollToTop = (options = {}) => {
    const {
      behavior = 'auto',
      target = 'window' // 'window' | 'modal'
    } = options;

    if (target === 'window') {
      // ページスクロール
      if (typeof window !== 'undefined') {
        window.scrollTo({
          top: 0,
          left: 0,
          behavior
        });
        
        // ブラウザ互換性対応
        if (document.documentElement) {
          document.documentElement.scrollTop = 0;
        }
        
        if (document.body) {
          document.body.scrollTop = 0;
        }
      }
    } else if (target === 'modal') {
      // モーダル内スクロール
      const modalContent = document.querySelector('.quick-note-modal .max-h-96');
      if (modalContent) {
        modalContent.scrollTop = 0;
      }
    }
  };

  return {
    scrollToTop
  };
} 