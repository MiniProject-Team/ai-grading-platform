import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Children, useRef, useState } from 'react';

export default function UploadCarousel({ children }) {
  const track = useRef(null);
  const slides = Children.toArray(children);
  const [activeIndex, setActiveIndex] = useState(0);

  const updateActive = () => {
    const element = track.current;
    if (!element) return;
    const cards = Array.from(element.children);
    const nearest = cards.reduce((bestIndex, card, index) =>
      Math.abs(card.offsetLeft - element.scrollLeft) < Math.abs(cards[bestIndex].offsetLeft - element.scrollLeft) ? index : bestIndex, 0);
    setActiveIndex(nearest);
  };

  const goTo = (index) => {
    const card = track.current?.children[index];
    if (card) track.current.scrollTo({ left: card.offsetLeft, behavior: 'smooth' });
  };

  return <section className="upload-carousel" aria-label="Evaluation files">
    <div className="upload-carousel-controls">
      <span aria-live="polite">File {activeIndex + 1} of {slides.length}</span>
      <div>
        <button className="icon-button" type="button" aria-label="Previous file section" onClick={() => goTo(Math.max(0, activeIndex - 1))} disabled={activeIndex === 0}><ChevronLeft aria-hidden="true" /></button>
        <button className="icon-button" type="button" aria-label="Next file section" onClick={() => goTo(Math.min(slides.length - 1, activeIndex + 1))} disabled={activeIndex === slides.length - 1}><ChevronRight aria-hidden="true" /></button>
      </div>
    </div>
    <div className="upload-grid" ref={track} onScroll={updateActive}>
      {slides.map((slide, index) => <div className="upload-slide" key={index}>{slide}</div>)}
    </div>
    <div className="upload-dots" aria-label="Choose a file section">
      {slides.map((_, index) => <button key={index} type="button" aria-label={`Show file section ${index + 1}`} aria-current={activeIndex === index ? 'step' : undefined} onClick={() => goTo(index)} />)}
    </div>
  </section>;
}
