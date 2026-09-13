import Chat from "./components/Chat";

export default function App() {
  return (
    <div className="page">
      <header className="page-header">
        <div className="brand">
          <span className="brand-mark">S</span>
          <div>
            <h1>Университет «Синергия»</h1>
            <p>Виртуальный помощник</p>
          </div>
        </div>
      </header>
      <main className="page-main">
        <Chat />
      </main>
      <footer className="page-footer">
        Чат-бот распознаёт ключевые слова и может оформить заявку на консультацию.
      </footer>
    </div>
  );
}
