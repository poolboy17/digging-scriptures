/**
 * ================================================================================
 * VIATOR AFFILIATE PRODUCTS — PILGRIMAGE SITES
 * ================================================================================
 * Sidebar product data for monetized pages (Places + Routes only).
 * Hub, Story, and Context pages NEVER show products.
 *
 * Tier structure:
 *   hero    — Top pick, shown with image card
 *   value   — Best value / budget-friendly option
 *   premium — Premium or private experience
 *
 * Affiliate: Viator partner ID P00166886
 * ================================================================================
 */

export interface SidebarProduct {
  title: string;
  url: string;
  image?: string;
  tier: 'hero' | 'value' | 'premium';
  price?: string;
  rating?: number;
  reviews?: number;
  label?: string;
  duration?: string;
}

// ================================================================================
// PLACE PRODUCTS — keyed by content slug
// ================================================================================

export const PLACE_PRODUCTS: Record<string, SidebarProduct[]> = {

  'jerusalem-old-city': [
    {
      title: 'Jerusalem Old City Walking Tour with Holy Sepulchre',
      url: 'https://www.viator.com/tours/Jerusalem/Old-City-Jerusalem-Walking-Tour/d932-5765JERUSALEM?pid=P00166886&mcid=42383',
      image: 'https://media-cdn.tripadvisor.com/media/attractions-splice-spp-720x480/0b/27/a6/4e.jpg',
      price: '$60',
      rating: 4.8,
      reviews: 1243,
      duration: '3 hours',
      tier: 'hero',
    },
    {
      title: 'Jerusalem Highlights: Self-Guided Audio Tour',
      url: 'https://www.viator.com/tours/Jerusalem/Jerusalem-Highlights-Self-Guided-Audio-Tour/d932-222222P89?pid=P00166886&mcid=42383',
      price: '$10',
      rating: 4.5,
      reviews: 87,
      duration: 'Self-guided',
      tier: 'value',
      label: 'Budget Friendly',
    },
    {
      title: 'Private Guide: Jerusalem Holy Sites Full Day',
      url: 'https://www.viator.com/tours/Jerusalem/Private-Tour-Jerusalem-Full-Day/d932-46862P2?pid=P00166886&mcid=42383',
      image: 'https://media-cdn.tripadvisor.com/media/attractions-splice-spp-720x480/07/25/6c/4e.jpg',
      price: '$350',
      rating: 5.0,
      reviews: 312,
      duration: '8 hours',
      tier: 'premium',
      label: 'Private Guide',
    },
  ],

  'santiago-de-compostela': [
    {
      title: 'Santiago de Compostela Walking Tour with Cathedral Visit',
      url: 'https://www.viator.com/tours/Santiago-de-Compostela/Walking-Tour-Cathedral/d5469-17232P8?pid=P00166886&mcid=42383',
      image: 'https://media-cdn.tripadvisor.com/media/attractions-splice-spp-720x480/0a/3b/20/c4.jpg',
      price: '$18',
      rating: 4.7,
      reviews: 856,
      duration: '2 hours',
      tier: 'hero',
    },
    {
      title: 'Santiago de Compostela Self-Guided Audio Tour',
      url: 'https://www.viator.com/tours/Santiago-de-Compostela/Self-Guided-Audio-Tour/d5469-259665P20?pid=P00166886&mcid=42383',
      price: '$8',
      rating: 4.3,
      reviews: 42,
      duration: 'Self-guided',
      tier: 'value',
      label: 'Budget Friendly',
    },
    {
      title: 'Private Tour: Santiago de Compostela with Gastronomy',
      url: 'https://www.viator.com/tours/Santiago-de-Compostela/Private-Tour-with-Gastronomy/d5469-66194P1?pid=P00166886&mcid=42383',
      price: '$190',
      rating: 4.9,
      reviews: 128,
      duration: '4 hours',
      tier: 'premium',
      label: 'Private Guide',
    },
  ],
};

// ================================================================================
// ROUTE PRODUCTS — keyed by content slug
// ================================================================================

export const ROUTE_PRODUCTS: Record<string, SidebarProduct[]> = {

  'camino-de-santiago': [
    {
      title: 'Last 100km of the Camino de Santiago: 7-Day Walking Tour',
      url: 'https://www.viator.com/tours/Santiago-de-Compostela/Camino-de-Santiago-Last-100km/d5469-19297P4?pid=P00166886&mcid=42383',
      image: 'https://media-cdn.tripadvisor.com/media/attractions-splice-spp-720x480/06/6f/aa/d5.jpg',
      price: '$789',
      rating: 4.8,
      reviews: 234,
      duration: '7 days',
      tier: 'hero',
      label: 'Most Popular',
    },
    {
      title: 'Camino de Santiago: Last 5 Stages Self-Guided',
      url: 'https://www.viator.com/tours/Santiago-de-Compostela/Camino-Last-5-Stages/d5469-39281P1?pid=P00166886&mcid=42383',
      price: '$420',
      rating: 4.6,
      reviews: 97,
      duration: '5 days',
      tier: 'value',
      label: 'Self-Guided',
    },
    {
      title: 'Private Camino: Premium Walking with Luggage Transfer',
      url: 'https://www.viator.com/tours/Santiago-de-Compostela/Private-Camino-Premium/d5469-85432P1?pid=P00166886&mcid=42383',
      price: '$1,450',
      rating: 5.0,
      reviews: 43,
      duration: '8 days',
      tier: 'premium',
      label: 'Premium Private',
    },
  ],
};
