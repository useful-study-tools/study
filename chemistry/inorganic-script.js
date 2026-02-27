/**
 * 空欄をクリックした際に、中身を表示・非表示にする関数
 * @param {HTMLElement} element - クリックされたli要素
 */
function reveal(element) {
    const blank = element.querySelector('.blank');
    if (blank) {
        blank.classList.toggle('revealed');
    }
}

/**
 * ページトップへスムーズにスクロールする関数
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * スクロール位置に応じて「トップへ戻る」ボタンの表示を切り替え
 */
window.onscroll = function() {
    const topButton = document.getElementById("backToTop");
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        topButton.style.display = "flex";
    } else {
        topButton.style.display = "none";
    }
};
