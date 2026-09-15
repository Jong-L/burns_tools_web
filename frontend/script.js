// 获取页面元素
const counterEl = document.getElementById('counter');
const btnInc = document.getElementById('btn-inc');
const btnDec = document.getElementById('btn-dec');
const btnReset = document.getElementById('btn-reset');

let count = 0;

// 更新显示
function render() {
  counterEl.textContent = count;
}

// 绑定按钮事件
btnInc.addEventListener('click', () => {
  count++;
  render();
});

btnDec.addEventListener('click', () => {
  count--;
  render();
});

btnReset.addEventListener('click', () => {
  count = 0;
  render();
});

render();
