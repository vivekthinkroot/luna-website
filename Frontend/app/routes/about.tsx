
import { useLocation, useParams } from 'react-router';
import AboutUs from '../components/AboutUs'

export default function PricingPage() {
    const url = useLocation();
    const section = url?.pathname?.split('/')[1]
    console.log('route: ', section)
    switch (section) {
        case 'about':
            return <AboutUs />;
        default:
            return <div>Section not found</div>;
    }
}
