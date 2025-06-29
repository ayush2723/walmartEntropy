import { mockProducts } from '../data/mockData';

export interface ChatResponse {
  message: string;
  products?: Array<{
    id: string;
    name: string;
    price: number;
    image: string;
    category: string;
    deal?: {
      discount: number;
      originalPrice: number;
    };
  }>;
  suggestions?: string[];
}

export class ChatbotService {
  private static instance: ChatbotService;
  private conversationHistory: string[] = [];

  static getInstance(): ChatbotService {
    if (!ChatbotService.instance) {
      ChatbotService.instance = new ChatbotService();
    }
    return ChatbotService.instance;
  }

  private analyzeIntent(message: string): {
    intent: string;
    entities: string[];
    confidence: number;
  } {
    const lowerMessage = message.toLowerCase();
    
    // Category detection
    const categories = {
      groceries: ['grocery', 'groceries', 'food', 'eat', 'cooking', 'kitchen', 'fresh', 'organic', 'fruit', 'vegetable', 'meat', 'dairy', 'bread', 'milk', 'cheese'],
      electronics: ['electronics', 'electronic', 'phone', 'smartphone', 'laptop', 'computer', 'headphones', 'tech', 'gadget', 'device'],
      clothing: ['clothing', 'clothes', 'shirt', 'pants', 'dress', 'shoes', 'fashion', 'wear', 'outfit'],
      home: ['home', 'house', 'furniture', 'decor', 'kitchen', 'bedroom', 'living room', 'appliance', 'lamp', 'blender']
    };

    // Intent detection
    const intents = {
      search_product: ['looking for', 'need', 'want', 'find', 'search', 'show me', 'get me'],
      price_inquiry: ['cheap', 'expensive', 'budget', 'affordable', 'cost', 'price', 'money'],
      deal_inquiry: ['deal', 'deals', 'discount', 'sale', 'offer', 'promotion', 'bargain'],
      recommendation: ['recommend', 'suggest', 'advice', 'help', 'what should', 'best'],
      greeting: ['hi', 'hello', 'hey', 'good morning', 'good afternoon'],
      waste_reduction: ['eco', 'environment', 'waste', 'sustainable', 'green', 'expiring']
    };

    let detectedIntent = 'general';
    let confidence = 0.5;
    const entities: string[] = [];

    // Detect intent
    for (const [intent, keywords] of Object.entries(intents)) {
      const matches = keywords.filter(keyword => lowerMessage.includes(keyword));
      if (matches.length > 0) {
        detectedIntent = intent;
        confidence = Math.min(0.9, 0.6 + (matches.length * 0.1));
        break;
      }
    }

    // Detect categories
    for (const [category, keywords] of Object.entries(categories)) {
      const matches = keywords.filter(keyword => lowerMessage.includes(keyword));
      if (matches.length > 0) {
        entities.push(category);
      }
    }

    return { intent: detectedIntent, entities, confidence };
  }

  private getProductsByCategory(category: string, limit: number = 4) {
    return mockProducts
      .filter(product => product.category === category)
      .slice(0, limit)
      .map(product => ({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        category: product.category,
        deal: product.deal
      }));
  }

  private getDealsProducts(limit: number = 4) {
    return mockProducts
      .filter(product => product.deal)
      .slice(0, limit)
      .map(product => ({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        category: product.category,
        deal: product.deal
      }));
  }

  private getBudgetProducts(limit: number = 4) {
    return mockProducts
      .filter(product => product.price < 50)
      .sort((a, b) => a.price - b.price)
      .slice(0, limit)
      .map(product => ({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        category: product.category,
        deal: product.deal
      }));
  }

  private getWasteReductionProducts(limit: number = 4) {
    return mockProducts
      .filter(product => product.deal?.type === 'waste-reduction' || product.deal?.type === 'flash')
      .slice(0, limit)
      .map(product => ({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        category: product.category,
        deal: product.deal
      }));
  }

  generateResponse(userMessage: string): ChatResponse {
    this.conversationHistory.push(userMessage);
    const analysis = this.analyzeIntent(userMessage);
    
    let response: ChatResponse = {
      message: "I understand you're looking for products. Could you be more specific about what you need?",
      suggestions: ["Show me groceries", "Any deals today?", "Looking for electronics", "Budget-friendly items"]
    };

    switch (analysis.intent) {
      case 'greeting':
        response = {
          message: "Hello! Welcome to Walmart! I'm here to help you find the best products and deals. What are you looking for today?",
          suggestions: ["Show me today's deals", "I need groceries", "Electronics on sale", "Budget shopping"]
        };
        break;

      case 'search_product':
        if (analysis.entities.length > 0) {
          const category = analysis.entities[0];
          const products = this.getProductsByCategory(category);
          response = {
            message: `Great! I found some excellent ${category} products for you. Here are my top recommendations:`,
            products,
            suggestions: [`More ${category} items`, "Show me deals", "Budget options", "Premium products"]
          };
        } else {
          response = {
            message: "I'd love to help you find products! What category are you interested in?",
            suggestions: ["Groceries", "Electronics", "Clothing", "Home & Garden"]
          };
        }
        break;

      case 'deal_inquiry':
        const dealProducts = this.getDealsProducts();
        response = {
          message: "Fantastic! I've found some amazing deals for you. Our SmartWaste AI has identified these special offers:",
          products: dealProducts,
          suggestions: ["More deals", "Flash sales", "Eco-friendly deals", "Grocery discounts"]
        };
        break;

      case 'price_inquiry':
        const budgetProducts = this.getBudgetProducts();
        response = {
          message: "Perfect! I've found some great budget-friendly options for you. These products offer excellent value:",
          products: budgetProducts,
          suggestions: ["More budget items", "Clearance deals", "Bulk savings", "Generic brands"]
        };
        break;

      case 'waste_reduction':
        const ecoProducts = this.getWasteReductionProducts();
        response = {
          message: "Excellent choice! Here are some eco-friendly deals from our SmartWaste AI system. These products help reduce waste while saving you money:",
          products: ecoProducts,
          suggestions: ["More eco deals", "Expiring soon items", "Donation program", "Sustainability info"]
        };
        break;

      case 'recommendation':
        if (analysis.entities.length > 0) {
          const category = analysis.entities[0];
          const products = this.getProductsByCategory(category, 3);
          response = {
            message: `Based on your interest in ${category}, here are my top recommendations:`,
            products,
            suggestions: [`Best ${category} deals`, "Customer favorites", "New arrivals", "Premium options"]
          };
        } else {
          // Recommend based on conversation history
          const products = this.getDealsProducts(3);
          response = {
            message: "Based on current trends and deals, here are my top recommendations for you:",
            products,
            suggestions: ["Personalized picks", "Trending now", "Customer favorites", "Best sellers"]
          };
        }
        break;

      default:
        // Try to extract category from general message
        if (analysis.entities.length > 0) {
          const category = analysis.entities[0];
          const products = this.getProductsByCategory(category);
          response = {
            message: `I found some great ${category} products that might interest you:`,
            products,
            suggestions: [`More ${category}`, "Compare prices", "Customer reviews", "Similar items"]
          };
        }
        break;
    }

    return response;
  }

  getConversationContext(): string[] {
    return this.conversationHistory.slice(-5); // Last 5 messages for context
  }

  clearHistory(): void {
    this.conversationHistory = [];
  }
}