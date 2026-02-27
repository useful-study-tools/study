// 空欄の表示切り替え
function reveal(element) {
    const blank = element.querySelector('.blank');
    if (blank) {
        blank.classList.toggle('revealed');
    }
}

// スムーズスクロール
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ボタンの表示制御
window.onscroll = function() {
    const btn = document.getElementById("backToTop");
    if (document.documentElement.scrollTop > 300) {
        btn.style.display = "flex";
    } else {
        btn.style.display = "none";
    }
};
