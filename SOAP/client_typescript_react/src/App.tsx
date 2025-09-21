import { lazy } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';

const HomePage = lazy(() => import("./pages/home"));

function App() {
  return <>
    <BrowserRouter>
        <Routes>
          <Route path='/' element={<HomePage />} />
        </Routes>
    </BrowserRouter>
  </>;
}

export default App;
